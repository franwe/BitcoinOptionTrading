import numpy as np

from spd_trading import risk_neutral_density as rnd
from spd_trading import historical_density as hd
from spd_trading import kernel as ker

from util.general import create_dates, load_tau_section_parameters
from util.data import RndData, HdData, Bandwidth, save_rnd_hd
from util.configcore import config


import logging

logging.basicConfig(level=logging.WARNING, filename="rnd_hd_corrected.log")

# -----------------------------------------------------------------------------
def plot_MKM(
    bwTable,
    RndData,
    HdData,
    day,
    tau_day,
    x,
    overwrite_RND=True,
    overwrite_GARCH=False,
    overwrite_simulations=False,
    save=False,
):
    filename = f"T-{tau_day}_{day}_corrected.png"

    df_tau = RndData.filter_data(date=day, tau_day=tau_day, mode="unique")
    hd_data, S0_binance = HdData.filter_data(day)
    S0 = HdData.get_S0(day)
    print(f"--------------------- {df_tau.shape}, {S0}, {day}, {tau_day}")

    mask = (bwTable.bw_original.date == day) & (bwTable.bw_original.tau_day == tau_day)
    _, _, h_m, h_m2, h_k = bwTable.table[mask].values[0]
    _, _, h_m_org, h_m2_org, h_k_org = bwTable.bw_original[mask].values[0]
    if all([h_m != h_m_org, h_k != h_k_org, h_m2 != h_m2_org]):
        logging.warning(f"All bandwidths adjusted for: {day}, {tau_day}")

    RND = rnd.Calculator(
        data=df_tau,
        tau_day=tau_day,
        date=day,
        sampling=config.model_config.sampling,
        n_sections=config.model_config.n_sections,
        loss=config.model_config.loss,
        kernel=config.model_config.kernel,
        overwrite_RND=overwrite_RND,
        data_folder=config.app_config.data_rnd,
        h_m=h_m,
        h_m2=h_m2,
        h_k=h_k,
    )
    RND.get_rnd()

    # algorithm plot
    RndPlot = rnd.Plot()
    fig_method = RndPlot.rookleyMethod(RND)

    HD = hd.Calculator(
        data=hd_data,
        tau_day=tau_day,
        date=day,
        S0=S0,
        garch_data_folder=config.app_config.data_garch,
        n_fits=config.model_config.n_fits,
        cutoff=config.model_config.cutoff,
        overwrite_model=overwrite_GARCH,
        overwrite_simulations=overwrite_simulations,
        window_length=config.model_config.window_length,
        simulations=config.model_config.simulations,
    )
    HD.get_hd(variate_GARCH_parameters=True)

    Kernel = ker.Calculator(
        tau_day=tau_day,
        date=day,
        RND=RND,
        HD=HD,
        similarity_threshold=config.model_config.similarity_threshold,
        cut_tail_percent=config.model_config.cut_tail_percent,
    )
    Kernel.calc_kernel()
    Kernel.calc_trading_intervals()

    TradingPlot = ker.Plot()  # kernel plot - comparison of rnd and hd
    fig_strategy = TradingPlot.kernelplot(Kernel)

    if save:
        save_rnd_hd(day, tau_day, RND, HD, Kernel)

    return fig_method, fig_strategy, filename


# ------------------------------------------------------------------------ MAIN
# ------------------------------------------------------------------------ MAIN
# ------------------------------------------------------------------------ MAIN
HdData = HdData()
RndData = RndData(cutoff=config.model_config.cutoff)

bwTable = Bandwidth()
bwTable.get_table()

# ------------------------------------------------------------ CALCULATE RND HD
(_, _, _, tau_min, tau_max) = load_tau_section_parameters(config.model_config.tau_section)

days = create_dates(start="2020-03-01", end="2020-09-30")
for day in days:
    print(day)
    taus = RndData.analyse(day)
    for tau in taus:
        tau_day = tau["_id"]
        if (tau_day > tau_min) & (tau_day <= tau_max) & (tau["count"] > 25):
            try:
                fig_method, fig_strategy, filename = plot_MKM(
                    bwTable,
                    RndData,
                    HdData,
                    day,
                    tau_day,
                    x=config.model_config.cutoff,
                    overwrite_RND=True,
                    overwrite_GARCH=False,
                    overwrite_simulations=False,
                    save=True,
                )
                fig_method.savefig(
                    config.app_config.plot_dir.joinpath("RND", filename),
                    transparent=True,
                )
                fig_strategy.savefig(
                    config.app_config.plot_dir.joinpath("kernel", filename),
                    transparent=True,
                )
            except ValueError as e:
                print("ValueError  : ", e, day, tau_day)
            except np.linalg.LinAlgError as e:
                print("np.linalg.LinAlgError :  ", e)
                print("cant invert matrix, smoothing_rookley")
            except ZeroDivisionError as e:
                print("ZeroDivisionError  : ", e)
                print("Empty data.")
