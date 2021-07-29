import pandas as pd
import logging

from util.general import create_dates, load_tau_section_parameters, add_days
from util.data import RndData, load_rnd_hd, save_trades
from util.configcore import config

import util.trading as tng

pd.options.mode.chained_assignment = None  # default='warn'

# BUG: count intervals - K1/K2 takes also 4 intervals?
# TODO: check if "total" is farther at the front of table
# TODO: plots x-axis "Probability" not "Density"
# ----------------------------------------------------------- LOAD DATA hd_curve, RND

(
    filename,
    near_bound,
    far_bound,
    tau_min,
    tau_max,
) = load_tau_section_parameters(config.model_config.tau_section)

df_results = pd.DataFrame(
    columns=[
        "date",
        "tau_day",
        "maturity_day",
        "total",
        "t0_payoff",
        "T_payoff",
        "trade",
        "kernel",
    ]
)
RndData = RndData(cutoff=config.model_config.cutoff)
days = create_dates(start="2020-03-01", end="2020-09-30")
for day in days:
    taus = RndData.analyse(day)
    for tau in taus:
        tau_day = tau["_id"]
        if (tau_day > tau_min) & (tau_day <= tau_max):
            print(tau_day, day)

            # load what is needed for density and kernel-plot. If does not exist, break
            try:
                (RND, HD, Kernel) = load_rnd_hd(day, tau_day)
                Kernel.similarity_threshold = config.model_config.similarity_threshold
                Kernel.calc_trading_intervals()
                RND.data = RndData.add_option_color(RND.data)
            except FileNotFoundError:
                logging.info(day, tau_day, " ---- densities do not exist")
                break

            # -------------------------- LOAD OPTIONS THAT ARE OFFERED NEXT DAY
            trading_day = add_days(day, 1)
            trading_tau = tau_day - 1

            try:
                df_trading = RndData.filter_data(date=trading_day, tau_day=trading_tau, mode="unique")
                df_trading = RndData.add_option_color(df_trading)
            except AttributeError:
                logging.info(f"{trading_day}, {trading_tau} ---- missing data for trading day")
                break

            try:
                OptionEvaluator = tng.OptionEvaluator(trading_day, trading_tau, data=df_trading)
                OptionEvaluator.execute_options()
            except KeyError:
                logging.info(f"{trading_day}, {trading_tau} ---- Maturity not reached yet")
                break
            except ValueError:
                logging.info(f"{trading_day}, {trading_tau} ---- DataFrame Empty, (cutoff)")
                break

            # ------------------------- TRY IF FIND RESULT FOR TRADING STRATEGY
            results_tmp = {}
            Strategies = tng.Strategies(
                OptionEvaluator,
                trading_intervals=Kernel.trading_intervals,
                moneyness_bound=near_bound,
                moneyness_range=RND.q_M["x"],
            )
            for name, strategy in zip(
                ["S1", "S2", "K1", "K2"],
                [Strategies.S1, Strategies.S2, Strategies.K1, Strategies.K2],
            ):
                df_trades = strategy()
                results_tmp.update({name: df_trades})
            results = {k: v for k, v in results_tmp.items() if v is not None}
            print(trading_day, trading_tau, results.keys())

            # ----------------------------------------- KERNEL DEVIATES FROM 1?
            around_one = (Kernel.kernel["y"] > 1 - config.model_config.similarity_threshold) & (
                Kernel.kernel["y"] < 1 + config.model_config.similarity_threshold
            )
            deviates_from_one_ratio = 1 - around_one.sum() / len(Kernel.kernel["x"])

            df_results = tng.add_results_to_table(
                df_results=df_results,
                results=results,
                trading_day=trading_day,
                trading_tau=trading_tau,
                maturity_day=OptionEvaluator.maturity_day,
                deviates_from_one_ratio=deviates_from_one_ratio,
                hd_K=HD.q_K,
                M=OptionEvaluator.S0 / OptionEvaluator.ST,
            )
            save_trades(
                trading_day=trading_day,  # evaluation day?
                trading_tau=trading_tau,  # evaluation tau?
                maturity_day=OptionEvaluator.maturity_day,
                RND_table_densities=RND.data[["M", "option", "color", "q_M"]],
                RND_table_trades=OptionEvaluator.data,
                rnd=RND,
                hd=HD,
                Kernel=Kernel,
                trading_results=results,
                S0=OptionEvaluator.S0,
            )


df_results.to_csv(config.app_config.data_trades.joinpath(filename), index=False)

df = pd.DataFrame()
for filename in [
    "trades_smallTau.csv",
    "trades_bigTau.csv",
    "trades_hugeTau.csv",
]:
    df_tau = pd.read_csv(config.app_config.data_trades.joinpath(filename))
    df = df.append(df_tau, ignore_index=True)

df = df.round(2)
df = df.sort_values(by=["date", "tau_day"])
df["id"] = range(0, df.shape[0])
df.to_csv(config.app_config.data_trades.joinpath("trades.csv"))
