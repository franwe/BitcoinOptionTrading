import pandas as pd
import os
from datetime import datetime, timedelta

from util.data_processing import data_processing
from util.connect_db import connect_db, get_as_df, bulk_write

cwd = os.getcwd() + os.sep
data_path = cwd + "data" + os.sep

db = connect_db()
collection = db["deribit_transactions"]

# cursor = collection.aggregate([
#     { "$group": {
#         '_id': None,
#         "max": { "$max": "$timestamp" },
#         "min": { "$min": "$timestamp" }
#     }}
# ])
# print(list(cursor))

dates = pd.date_range("2020-03-04", "2020-09-30")
for start in dates:
    print(start)
    end = start + timedelta(days=1)  # datetime(2020,3,5)
    start_ts = int(datetime.timestamp(start) * 1000)
    end_ts = int(datetime.timestamp(end) * 1000)

    query = {
        "$and": [
            {"timestamp": {"$gte": start_ts}},
            {"timestamp": {"$lte": end_ts}},
        ]
    }
    df_all = get_as_df(collection, query)

    try:
        df_all["datetime"] = df_all.timestamp.apply(
            lambda ts: datetime.fromtimestamp(ts / 1000.0)
        )
        df_all["date"] = df_all.datetime.apply(lambda d: datetime.date(d))
        df_all["time"] = df_all.datetime.apply(lambda d: datetime.time(d))

        # -------------------------------------------------------- MERGE TRADES
        coll = db["trades_clean"]
        columns = [
            "timestamp",
            "iv",
            "instrument_name",
            "index_price",
            "direction",
            "date",
            "time",
            "price",
        ]
        trades = df_all.groupby(by=columns).count().reset_index()[columns]
        trades = data_processing(trades)
        bulk_write(coll=coll, df=trades, ordered=False)
        # write_in_db(coll=coll, df=trades)

        # ------------------------------------------------------------- MERGE S
        coll = db["BTCUSD"]
        columns = ["index_price", "datetime", "date", "time"]
        S = df_all.groupby(by=columns).count().reset_index()[columns]
        S["_id"] = S.apply(
            lambda row: str(row.date) + "_" + str(row.time), axis=1
        )
        S = S.sort_values(by="_id").reset_index()[["_id"] + columns]
        S["date"] = S.date.apply(lambda dt: str(dt))
        bulk_write(coll=coll, df=S, ordered=False)
        # write_in_db(coll=coll, df=S)

    except AttributeError as e:
        print(e)
        print("----- Date does not exist: ----- ", start.date())
