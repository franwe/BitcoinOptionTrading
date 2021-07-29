import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from util.general import create_dates
from util.general import add_days
from util.configcore import config
from util.data import RndData


def group_dataframe_by_date(df, which_date, mode="all_dates"):
    df_group = df[[which_date, "t0_payoff", "T_payoff", "total"]].groupby(by=which_date).sum().reset_index()

    df_group[which_date] = df_group[which_date].apply(lambda s: datetime.strptime(s, "%Y-%m-%d"))
    df_group["count"] = df[[which_date, "total"]].groupby(by=which_date).count().reset_index()["total"]
    df_group["mean"] = df_group["total"] / df_group["count"]

    if mode == "only_expiration_dates":
        return df_group
    date_frame = pd.date_range(df[which_date].min(), df[which_date].max(), freq="d")
    time = pd.DataFrame(data=date_frame, columns=[which_date])
    return pd.merge(time, df_group, on=which_date, how="left")


# ------------------------------------------------------------ CASHFLOW BARPLOT

df = pd.read_csv(config.app_config.data_trades.joinpath("trades.csv"))
print(
    df.groupby(by="trade")
    .sum()
    .reset_index()[["trade", "kernel", "total", "t0_payoff", "T_payoff"]]
    .to_latex(index=False)
)

a = group_dataframe_by_date(df, which_date="date")

# ---- find missing days

RndData = RndData(cutoff=0.5)
days = create_dates(start="2020-03-01", end="2020-09-30")

previous_date_exists = False
start_interval = 0
intervals = []
trading_days_count = 0
for day in days:
    taus = RndData.analyse(day)
    if len(taus) == 0:
        if previous_date_exists == True:
            print("start interval", day)
            start_interval = datetime.strptime(day, "%Y-%m-%d")
        elif previous_date_exists == False:
            # inside of interval
            b = 1
        previous_date_exists = False
    elif len(taus) > 0:
        trading_days_count += 1
        if previous_date_exists == False:
            print("end interval", start_interval, day)
            end_interval = datetime.strptime(day, "%Y-%m-%d")
            intervals.append((start_interval, end_interval))
        elif previous_date_exists == True:
            # outside of interval
            b = 1
        previous_date_exists = True
print(trading_days_count)
# ------------

no_data = intervals[1:]

fig, (ax0, ax1, ax2) = plt.subplots(3, 1, figsize=(8, 4), sharex=True)
plt.xticks(rotation=45)
ax0.bar(a.date, a.total, color="b")
ax1.bar(a.date, a.t0_payoff, color="k", alpha=0.5)
ax2.bar(a.date, a.T_payoff, color="k", alpha=0.5)
for text, ax in zip(["total", "trading day", "execution day"], [ax0, ax1, ax2]):
    for interval in no_data:
        ax.axvspan(interval[0], interval[1], color="grey", alpha=0.15)
    ax.set_ylim(-12000, 17000)
    # ax.set_xlim(a.date.min(), a.date.max())
    ax.set_xlim(datetime.strptime("2020-03-01", "%Y-%m-%d"), datetime.strptime("2020-10-01", "%Y-%m-%d"))
    ax.text(
        0.01,
        0.95,
        text,
        horizontalalignment="left",
        verticalalignment="top",
        transform=ax.transAxes,
    )

locator = mdates.AutoDateLocator(minticks=5, maxticks=10)
formatter = mdates.ConciseDateFormatter(locator)

ax2.xaxis.set_major_locator(locator)
ax2.xaxis.set_major_formatter(formatter)
ax2.set_xlabel("Trading Day")
ax1.set_ylabel("USD")
plt.tight_layout()

plt.show()
fig.savefig(config.app_config.plot_dir.joinpath("trading_payoffs.png"), transparent=True)

# ------------------------------------------------------------ Payoff by Expiration Date

a_maturity = group_dataframe_by_date(df, which_date="maturity_day", mode="only_expiration_dates")


fig, (ax0) = plt.subplots(1, 1, figsize=(8, 2))
plt.xticks(rotation=45)
ax0.bar(a_maturity.maturity_day, a_maturity.total, color="b", width=5, alpha=0.5)
locator = mdates.AutoDateLocator(minticks=5, maxticks=10)
formatter = mdates.ConciseDateFormatter(locator)
ax0.xaxis.set_major_locator(locator)
ax0.xaxis.set_major_formatter(formatter)
ax0.set_xlabel("Expiration Day")
ax0.set_ylabel("USD")
ax0.set_xlim(datetime.strptime("2020-03-01", "%Y-%m-%d"), datetime.strptime("2020-12-31", "%Y-%m-%d"))
plt.tight_layout()

a = 1
