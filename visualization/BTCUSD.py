from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

import pandas as pd
from datetime import datetime
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from util.connect_db import connect_db, get_as_df

from util.configcore import config

db = connect_db()


# ------------------------------------------------------------------------ PLOT
query = {}
query = {"datetime": {"$gte": datetime.timestamp(datetime.fromisoformat("2017-08-16")) * 1000}}

prices_deribit = get_as_df(db[config.app_config.BTCUSD_deribit], query)
prices_deribit["time_dt"] = prices_deribit.datetime.apply(lambda ts: datetime.fromtimestamp(ts / 1000))


prices_binance = get_as_df(db[config.app_config.BTCUSD_binance], query)
prices_binance["time_dt"] = prices_binance.datetime.apply(lambda ts: datetime.fromtimestamp(ts / 1000))

merged_prices = pd.merge(
    prices_deribit,
    prices_binance,
    how="left",
    on="time_dt",
    suffixes=("_deribit", "_binance"),
)

fig1 = plt.figure(figsize=(8, 3))
ax = fig1.add_subplot(111)
plt.xticks(rotation=45)

ax.plot(prices_binance.time_dt, prices_binance.price, "b", lw=1)
ax.scatter(merged_prices.time_dt, merged_prices.price_binance, s=4, c="b")
ax.scatter(merged_prices.time_dt, merged_prices.price_deribit, s=4, c="r")

# ----------------------------------------------------------------------- INSET
axins = ax.inset_axes([0.2, 0.5, 0.47, 0.47])
axins.plot(prices_binance.time_dt, prices_binance.price, "b", lw=1)
axins.scatter(merged_prices.time_dt, merged_prices.price_binance, s=4, c="b")
axins.scatter(merged_prices.time_dt, merged_prices.price_deribit, s=4, c="r")

start_date = datetime(2019, 12, 1)
end_date = datetime(2020, 4, 1)

axins.set_xlim(start_date, end_date)
axins.set_ylim(4400, 11000)
axins.set_xticklabels("")

ax.indicate_inset_zoom(axins)

# ----------------------------------------------------------------------- BOXEN

ax.axvspan(datetime(2020, 3, 6), datetime(2020, 9, 27), color="b", alpha=0.2)
ax.axvspan(datetime(2020, 9, 29), datetime(2021, 1, 15), color="b", alpha=0.1)
locator = mdates.AutoDateLocator(minticks=5, maxticks=10)
formatter = mdates.ConciseDateFormatter(locator)
ax.xaxis.set_major_locator(locator)
ax.xaxis.set_major_formatter(formatter)
ax.set_ylabel("BTCUSD")

plt.tight_layout()
plt.show()

fig1.savefig(config.app_config.plot_dir.joinpath("BTCUSD_comparison.png"), transparent=True)
