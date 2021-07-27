import pickle
import pandas as pd
from copy import deepcopy
import logging

from util.connect_db import connect_db, get_as_df
from util.configcore import config


class RndData:
    def __init__(self, cutoff):
        self.coll = connect_db()["trades_clean"]
        self.cutoff = cutoff

    def load_data(self, date_str):
        """Load all trades, with duplicates.
        It DOES make a difference in Fitting!"""
        x = self.cutoff
        query = {"date": date_str}
        d = get_as_df(self.coll, query)
        df = d[(d.M <= 1 + x) & (d.M > 1 - x)]
        df = df[(df.iv > 0.01)]
        self.complete = df

    def analyse(self, date=None, sortby="date"):
        if date is None:
            cursor = self.coll.aggregate(
                [
                    {"$group": {"_id": "$date", "count": {"$sum": 1}}},
                    {"$sort": {"_id": -1}},
                ]
            )
        else:
            cursor = self.coll.aggregate(
                [
                    {"$match": {"date": date}},
                    {"$group": {"_id": "$tau_day", "count": {"$sum": 1}}},
                    {"$sort": {"_id": 1}},
                ]
            )
        return list(cursor)

    def delete_duplicates(self):
        """
        Should I do it or not? It deletes if for same option was bought twice a
        day. I guess better not delete, because might help for fitting to have
        weight of more trades to the "normal" values.
        """
        self.unique = self.complete.drop_duplicates()

    def filter_data(self, date, tau_day, mode="unique"):
        self.load_data(date)
        if mode == "complete":
            filtered_by_date = self.complete
        elif mode == "unique":
            self.delete_duplicates()
            filtered_by_date = self.unique

        df_tau = filtered_by_date[(filtered_by_date.tau_day == tau_day)]
        df_tau = df_tau.reset_index()
        return df_tau

    def add_option_color(self, data):
        call_mask = data.option == "C"
        data["color"] = "blue"  # blue - put
        data.loc[call_mask, "color"] = "red"  # red - call
        return data


# ----------------------------------------------------------------------------------------------------------------- DATA
from datetime import datetime, timezone


def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))


def date_str2int(date_str):
    return int(date_str[:4]), int(date_str[5:7]), int(date_str[8:])


class HdData:
    def __init__(self, target="price"):
        self.target = target
        self.coll = connect_db()["BTCUSD_binance"]
        self.complete = None
        self._load_data()

    def _load_data(self):
        """Load complete BTCUSDT prices"""
        prices_binance = get_as_df(self.coll, {})
        self.complete = prices_binance

    def filter_data(self, date):
        S0 = self.complete.loc[self.complete.date_str == date, "price"].item()
        df = self.complete[self.complete.date_str <= date]
        return df, S0

    def get_S0(self, day):
        db = connect_db()
        coll = db["BTCUSD"]
        query = {"date": day}
        prices = get_as_df(coll, query)
        date = date_str2int(day)
        dt = datetime(date[0], date[1], date[2], 8, 0, 0, 0)
        ts_8 = dt.replace(tzinfo=timezone.utc).timestamp() * 1000

        ts_idx = nearest(prices.datetime, ts_8)
        S = prices[prices.datetime == ts_idx].index_price
        return S.to_list()[0]


class Bandwidth:
    def __init__(self):
        self.bw_original = pd.read_csv(config.app_config.bandwidths_table)
        self.table = None

    def replace_by_median(self, value, describe):
        if (value > describe["mean"] + describe["std"]) or (value < describe["mean"] - describe["std"]):
            value = describe["50%"]
        return value

    def replace_by_bound(self, value, describe):
        if value > describe["75%"]:
            value = describe["75%"]
        elif value < describe["25%"]:
            value = describe["25%"]
        return value

    def replace_lower(self, value, describe):
        if value < describe["25%"]:
            value = describe["50%"]
        return value

    def get_table(self):
        self.table = deepcopy(self.bw_original)
        cols = ["h_m", "h_m2"]
        for col in cols:
            desc_stat = self.bw_original[col].describe()
            logging.info(desc_stat)
            self.table[col] = self.bw_original[col].apply(lambda val: self.replace_by_bound(val, desc_stat))
            del desc_stat

        col = "h_k"
        desc_stat = self.bw_original[col].describe()
        logging.info(desc_stat)
        self.table[col] = self.bw_original[col].apply(lambda val: self.replace_lower(val, desc_stat))


# ----------------------------------------------------------- SAVE AND LOAD RND HD
def save_rnd_hd(day, tau_day, RND, HD, Kernel):
    data = {
        "date": day,
        "tau_day": tau_day,
        "RND": RND,
        "HD": HD,
        "Kernel": Kernel,
    }
    with open(
        config.app_config.data_densities.joinpath(f"T-{tau_day}_{day}.pkl"),
        "wb",
    ) as handle:
        pickle.dump(data, handle)


def load_rnd_hd(day, tau_day):
    with open(
        config.app_config.data_densities.joinpath(f"T-{tau_day}_{day}.pkl"),
        "rb",
    ) as handle:
        data = pickle.load(handle)
    RND = data["RND"]
    HD = data["HD"]
    Kernel = data["Kernel"]
    return RND, HD, Kernel


# ----------------------------------------------------------- TRADES - LOAD SAVE
def save_trades(
    trading_day,
    trading_tau,
    maturity_day,
    RND_table_densities,
    RND_table_trades,
    rnd,
    hd,
    Kernel,
    trading_results,
    S0,
):
    base_entry = {
        "day": trading_day,
        "tau_day": trading_tau,
        "trade": "-",
        "rnd": rnd,
        "RND_table_densities": RND_table_densities,
        "RND_table_trades": RND_table_trades,
        "hd": hd,
        "Kernel": Kernel,
        "trades": None,
        "S0": S0,
    }
    if len(trading_results) == 0:
        filename = f"T-{trading_tau}_{trading_day}_{'-'}.pkl"
        with open(config.app_config.data_trades.joinpath(filename), "wb") as handle:
            pickle.dump(base_entry, handle)
        return
    else:
        for trade in trading_results:
            trades = trading_results[trade]
            base_entry.update({"trades": trades})
            filename = f"T-{trading_tau}_{trading_day}_{trade}.pkl"
            with open(config.app_config.data_trades.joinpath(filename), "wb") as handle:
                pickle.dump(base_entry, handle)
    return


def load_trades(trading_day, trading_tau, trade):
    filename = f"T-{trading_tau}_{trading_day}_{trade}.pkl"
    print(f"load trades: {config.app_config.data_trades.joinpath(filename)}")
    with open(config.app_config.data_trades.joinpath(filename), "rb") as handle:
        data = pickle.load(handle)
    return data
