import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from util.connect_db import connect_db, get_as_df


class OptionEvaluator:
    def __init__(self, day, tau_day, data):
        self.day = day
        self.tau_day = tau_day
        self.data = self._format_data(data)  # data on trading_day
        self.S0 = None
        self.maturity_day = None
        self.ST = None

    def _format_data(self, data):
        df = data[
            [
                "M",
                "option",
                "P",
                "K",
                "S",
                "iv",
                "P_BTC",
                "color",
            ]
        ].sort_values(by="M")
        return df

    def _options_in_interval(self, option, moneyness, action, left, right):
        if (moneyness == "ATM") & (option == "C"):
            mon_left = 1 - self.moneyness_bound
            mon_right = 1 + self.moneyness_bound
            which_element = 0
        elif (moneyness == "ATM") & (option == "P"):
            mon_left = 1 - self.moneyness_bound
            mon_right = 1 + self.moneyness_bound
            which_element = -1

        elif (moneyness == "OTM") & (option == "C"):
            mon_left = 0
            mon_right = 1 - self.moneyness_bound
            which_element = -1
        elif (moneyness == "OTM") & (option == "P"):
            mon_left = 1 + self.moneyness_bound
            mon_right = 10
            which_element = 0

        candidates = self.data[
            (self.data.M > left)
            & (self.data.M < right)  # option interval
            & (self.data.M > mon_left)
            & (self.data.M < mon_right)
            & (self.data.option == option)
        ]
        candidate = candidates.iloc[which_element]
        candidate["action"] = action
        return candidate

    def _get_payoff(self, K, ST, option):
        if option == "C":
            return max(ST - K, 0)
        elif option == "P":
            return max(K - ST, 0)

    def execute_options(self):
        self.maturity_day = datetime.strptime(self.day, "%Y-%m-%d") + timedelta(days=self.tau_day)
        db = connect_db()

        coll = db["BTCUSD_deribit"]
        query = {"date_str": str(self.maturity_day.date())}
        self.ST = get_as_df(coll, query)["price"].item()

        query = {"date_str": self.day}
        self.S0 = get_as_df(coll, query)["price"].item()

        self.data["ST"] = self.ST
        self.data["opt_payoff"] = self.data.apply(lambda row: self._get_payoff(row.K, self.ST, row.option), axis=1)
        print(f"--- S0: {self.S0} --- ST: {self.ST} --- M: {self.S0 / self.ST}")

    def _calculate_fee(self, P, S, max_fee_BTC=0.0004, max_fee_pct=0.2):
        option_bound = max_fee_pct * P
        underlying_bound = max_fee_BTC * S
        fee = min(underlying_bound, option_bound)
        return fee

    def _payoff_call(self, action, K, price, ST):
        if action == "buy":
            return np.maximum(np.zeros(len(ST)), (ST - K)) - price
        elif action == "sell":
            return -1 * (np.maximum(np.zeros(len(ST)), (ST - K)) - price)

    def _payoff_put(self, action, K, price, ST):
        if action == "buy":
            return np.maximum(np.zeros(len(ST)), (K - ST)) - price
        elif action == "sell":
            return -1 * (np.maximum(np.zeros(len(ST)), (K - ST)) - price)

    def _get_option_buy_sell_payoff(self, option, action, K, price, ST):
        if option == "C":
            return {"S": ST, "payoff": self._payoff_call(action, K, price, ST)}
        elif option == "P":
            return {"S": ST, "payoff": self._payoff_put(action, K, price, ST)}

    def _get_trading_payoffs(self, data):
        """data is df_trades - only calculates the trading payoffs, does not evaluate all options"""
        buy_mask = data.action == "buy"

        data["trading_fee"] = data.apply(
            lambda row: self._calculate_fee(row.P, row.S, max_fee_BTC=0.0004),
            axis=1,
        )
        data["t0_payoff"] = data["P"]
        data.loc[buy_mask, "t0_payoff"] = -1 * data.loc[buy_mask, "P"]
        data["t0_payoff"] = data["t0_payoff"] - data["trading_fee"]

        data["T_payoff"] = -1 * data["opt_payoff"]
        data.loc[buy_mask, "T_payoff"] = +1 * data.loc[buy_mask, "opt_payoff"]
        data["delivery_fee"] = data.apply(
            lambda row: self._calculate_fee(row.T_payoff, row.S, max_fee_BTC=0.0002),
            axis=1,
        )
        data.loc[~buy_mask, "delivery_fee"] = 0  # only applies to TAKER ORDERS
        data["T_payoff"] = data["T_payoff"] - data["delivery_fee"]

        data["total"] = data.t0_payoff + data.T_payoff

        S = self.S0 / self.moneyness_range
        data["payoffs"] = data.apply(
            lambda row: self._get_option_buy_sell_payoff(row.option, row.action, row.K, row.P, S),
            axis=1,
        )
        return data


class Strategies(OptionEvaluator):
    def __init__(
        self,
        OptionEvaluator,
        trading_intervals,
        moneyness_bound,
        moneyness_range,
    ):
        self.data = OptionEvaluator.data
        self.S0 = OptionEvaluator.S0
        self.ST = OptionEvaluator.ST
        self.buy_intervals = trading_intervals["buy"]
        self.sell_intervals = trading_intervals["sell"]
        self.moneyness_bound = moneyness_bound
        self.moneyness_range = moneyness_range

    def K1(self):
        otm_call, otm_call_action = pd.Series(), "buy"
        otm_put, otm_put_action = pd.Series(), "buy"
        atm_call, atm_call_action = pd.Series(), "sell"
        atm_put, atm_put_action = pd.Series(), "sell"

        for interval in self.buy_intervals:
            left, right = interval
            try:
                otm_call = self._options_in_interval("C", "OTM", otm_call_action, left, right)
            except IndexError:
                pass

        for interval in self.sell_intervals:
            left, right = interval
            try:
                atm_call = self._options_in_interval(
                    "C",
                    "ATM",
                    atm_call_action,
                    left,
                    right,
                )
            except IndexError:
                pass

        for interval in self.sell_intervals:
            left, right = interval
            try:
                atm_put = self._options_in_interval(
                    "P",
                    "ATM",
                    atm_put_action,
                    left,
                    right,
                )
            except IndexError:
                pass

        for interval in self.buy_intervals:
            left, right = interval
            try:
                otm_put = self._options_in_interval(
                    "P",
                    "OTM",
                    otm_put_action,
                    left,
                    right,
                )
            except IndexError:
                pass

        if any([otm_call.empty, atm_call.empty, atm_put.empty, otm_put.empty]):
            pass
        else:
            df_trades = pd.DataFrame([otm_call, atm_call, atm_put, otm_put])
            return self._get_trading_payoffs(df_trades)

    def K2(self):
        otm_call, otm_call_action = pd.Series(), "sell"
        otm_put, otm_put_action = pd.Series(), "sell"
        atm_call, atm_call_action = pd.Series(), "buy"
        atm_put, atm_put_action = pd.Series(), "buy"

        for interval in self.sell_intervals:
            left, right = interval
            try:
                otm_call = self._options_in_interval("C", "OTM", otm_call_action, left, right)
            except IndexError:
                pass

        for interval in self.buy_intervals:
            left, right = interval
            try:
                atm_call = self._options_in_interval("C", "ATM", atm_call_action, left, right)
            except IndexError:
                pass

        for interval in self.buy_intervals:
            left, right = interval
            try:
                atm_put = self._options_in_interval("P", "ATM", atm_put_action, left, right)
            except IndexError:
                pass

        for interval in self.sell_intervals:
            left, right = interval
            try:
                otm_put = self._options_in_interval("P", "OTM", otm_put_action, left, right)
            except IndexError:
                pass

        if any([otm_call.empty, atm_call.empty, atm_put.empty, otm_put.empty]):
            pass
        else:
            df_trades = pd.DataFrame([otm_call, atm_call, atm_put, otm_put])
            return self._get_trading_payoffs(df_trades)

    def S1(self):
        otm_call, otm_call_action = pd.Series(), "buy"
        otm_put, otm_put_action = pd.Series(), "sell"

        for interval in self.buy_intervals:
            left, right = interval
            try:
                otm_call = self._options_in_interval("C", "OTM", otm_call_action, left, right)
            except IndexError:
                pass

        for interval in self.sell_intervals:
            left, right = interval
            try:
                otm_put = self._options_in_interval("P", "OTM", otm_put_action, left, right)
            except IndexError:
                pass

        if any([otm_call.empty, otm_put.empty]):
            pass
        elif (len(self.buy_intervals) > 1) or (len(self.sell_intervals) > 1):
            print(" ---- too many intervals")
            pass
        else:
            df_trades = pd.DataFrame([otm_call, otm_put])
            return self._get_trading_payoffs(df_trades)

    def S2(self):
        otm_call, otm_call_action = pd.Series(), "sell"
        otm_put, otm_put_action = pd.Series(), "buy"

        for interval in self.sell_intervals:
            left, right = interval
            try:
                otm_call = self._options_in_interval("C", "OTM", otm_call_action, left, right)
            except IndexError:
                pass

        for interval in self.buy_intervals:
            left, right = interval
            try:
                otm_put = self._options_in_interval("P", "OTM", otm_put_action, left, right)
            except IndexError:
                pass

        if any([otm_call.empty, otm_put.empty]):
            pass
        elif (len(self.buy_intervals) > 1) or (len(self.sell_intervals) > 1):
            print(" ---- too many intervals")
            pass
        else:
            df_trades = pd.DataFrame([otm_call, otm_put])
            return self._get_trading_payoffs(df_trades)


def _get_expected_payoff(payoff, density):
    weighted_payoff = payoff["payoff"] * density["y"]
    return weighted_payoff.mean(), {"S": payoff["S"], "payoff": weighted_payoff}


def add_results_to_table(
    df_results,
    results,
    trading_day,
    trading_tau,
    maturity_day,
    deviates_from_one_ratio,
    hd_K,
    M,
):
    base_entry = {
        "date": trading_day,
        "tau_day": trading_tau,
        "maturity_day": str(maturity_day.date()),
        "total": 0,
        "t0_payoff": 0,
        "T_payoff": 0,
        "trade": "-",
        "kernel": deviates_from_one_ratio,
        "M": M,
        "exp_total": None,
    }
    if len(results) == 0:
        df_results = df_results.append(base_entry, ignore_index=True)

    else:
        for key in results:
            df_trades = results[key]
            total = np.zeros(len(df_trades.payoffs.iloc[0]["payoff"]))
            for payoff in df_trades.payoffs:
                total += np.array(payoff["payoff"])
            total_payoff = {
                "S": payoff["S"],
                "payoff": total,
            }
            expected_payoff_mean, expected_payoff_values = _get_expected_payoff(total_payoff, hd_K)
            base_entry.update(
                {
                    "total": df_trades.total.sum(),
                    "t0_payoff": df_trades.t0_payoff.sum(),
                    "T_payoff": df_trades.T_payoff.sum(),
                    "trade": key,
                    "exp_total": expected_payoff_mean,
                }
            )
            df_results = df_results.append(base_entry, ignore_index=True)
    return df_results


# ---------------------------------------------------------- TRADING STRATEGIES
