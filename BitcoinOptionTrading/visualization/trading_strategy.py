from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from matplotlib import pyplot as plt
import numpy as np

from util.general import add_days
from util.data import load_trades
from util.configcore import config


# --------------------------------------------------------------- STRATEGY PLOT
trade_type = "S1"
trading_day = "2020-04-15"
trading_tau = 44

# calculate other days and tau
day = add_days(trading_day, -1)
tau_day = trading_tau + 1
execution_day = add_days(trading_day, trading_tau)

data = load_trades(trading_day=trading_day, trading_tau=trading_tau, trade=trade_type)
HD = data["hd"]
RND = data["rnd"]
rnd_points = data["RND_table_densities"]
K = data["Kernel"]
hd = K.hd_curve["y"]
rnd = K.rnd_curve["y"]
kernel = K.kernel["y"]
M = K.kernel["x"]
K_bound = K.similarity_threshold
M_bounds_buy = K.trading_intervals["buy"]
M_bounds_sell = K.trading_intervals["sell"]
df_all = data["RND_table_trades"]
df_trades = data["trades"]

# ---------------------------------------------------------------------- Figure
fig, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=(10, 3))
x_pos, y_pos = 0.99, 0.99
# ------------------------------------------------------------------- Densities
ax0.scatter(rnd_points.M, rnd_points.q_M, c=rnd_points.color, s=10)
ax0.plot(M, rnd, "r")
ax0.plot(M, hd, "b")
ax0.text(
    x_pos,
    y_pos,
    "evaluation day" + "\n" + str(day) + "\n" + r"$\tau$ = " + str(tau_day),
    horizontalalignment="right",
    verticalalignment="top",
    transform=ax0.transAxes,
)
ax0.set_xlabel("Moneyness")
ax0.set_ylabel("Risk Neutral Density")
ax0.set_xlim(0.5, 1.5)
ax0.set_ylim(0)

ax1.plot(M, kernel, "k")
ax1.axhspan(1 - K_bound, 1 + K_bound, color="grey", alpha=0.1)
for interval in M_bounds_buy:
    ax1.axvspan(interval[0], interval[1], color="r", alpha=0.1)

for interval in M_bounds_sell:
    ax1.axvspan(interval[0], interval[1], color="b", alpha=0.1)
ax1.scatter(df_all.M, [1] * len(df_all.M), c=df_all.color, s=10, alpha=0.1)
if not trade_type == "-":
    ax1.scatter(df_trades.M, [1] * len(df_trades.M), c=df_trades.color, s=50)
ax1.set_ylim(0, 2)
ax1.text(
    x_pos,
    y_pos,
    "trading day" + "\n" + str(trading_day) + "\n" + r"$\tau$ = " + str(trading_tau),
    horizontalalignment="right",
    verticalalignment="top",
    transform=ax1.transAxes,
)
ax1.set_xlabel("Moneyness")
ax1.set_ylabel("Kernel")
ax1.set_xlim(0.5, 1.5)

# --------------------------------------------------------------------- PAYOFFS
ymin, ymax = -1500, 1500
S0 = df_all.S.mean()
ST = df_all.ST.iloc[0]
ax2.vlines([S0, ST], ymin, ymax, colors=["darkgrey", "black"], ls=":")
total = np.zeros(len(df_trades.payoffs.iloc[0]["payoff"]))
for payoff, action in zip(df_trades.payoffs, df_trades.action):
    if action == "buy":
        ax2.plot(payoff["S"], payoff["payoff"], c="r", alpha=0.25)
    elif action == "sell":
        ax2.plot(payoff["S"], payoff["payoff"], c="b", alpha=0.25)
    total += np.array(payoff["payoff"])

ax2.plot(payoff["S"], total, c="k", lw=3)
ax2.hlines(0, payoff["S"].min(), payoff["S"].max(), color="grey", lw=1)
ax2.text(
    x_pos,
    y_pos,
    "execution day" + "\n" + execution_day,
    horizontalalignment="right",
    verticalalignment="top",
    transform=ax2.transAxes,
)
ax2.set_ylim(ymin, ymax)
ax2.set_xlabel("BTCUSD")
ax2.set_ylabel("Payoff")

plt.tight_layout()
plt.show()

fig.savefig(
    config.app_config.plot_dir.joinpath(f"trading_{trade_type}_{trading_day}_{trading_tau}.png"),
    transparent=True,
)
