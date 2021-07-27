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


trade_type = "K2"
trading_day = "2020-03-13"
trading_tau_1 = 14

# calculate other days and tau
day = add_days(trading_day, -1)
tau_day = trading_tau_1 + 1
execution_day = add_days(trading_day, trading_tau_1)

data = load_trades(trading_day=trading_day, trading_tau=trading_tau_1, trade=trade_type)
HD = data["hd"]
RND = data["rnd"]
rnd_points = data["RND_table_densities"]
K = data["Kernel"]
hd = K.hd_curve["y"]
rnd = K.rnd_curve["y"]
M = K.kernel["x"]


# ---------------------------------------------------------------------- Figure
fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(7, 3))
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
ax0.set_ylim(0, 3.22)


# ------------------------------------------------------------------- Densities
trade_type = "K2"
trading_day = "2020-03-13"
trading_tau_2 = 42

# calculate other days and tau
day = add_days(trading_day, -1)
tau_day = trading_tau_2 + 1
execution_day = add_days(trading_day, trading_tau_2)

data = load_trades(trading_day=trading_day, trading_tau=trading_tau_2, trade=trade_type)
HD = data["hd"]
RND = data["rnd"]
rnd_points = data["RND_table_densities"]
K = data["Kernel"]
hd = K.hd_curve["y"]
rnd = K.rnd_curve["y"]
M = K.kernel["x"]

ax1.scatter(rnd_points.M, rnd_points.q_M, c=rnd_points.color, s=10)
ax1.plot(M, rnd, "r")
ax1.plot(M, hd, "b")
ax1.text(
    x_pos,
    y_pos,
    "evaluation day" + "\n" + str(day) + "\n" + r"$\tau$ = " + str(tau_day),
    horizontalalignment="right",
    verticalalignment="top",
    transform=ax1.transAxes,
)
ax1.set_xlabel("Moneyness")
ax1.set_ylabel("Risk Neutral Density")
ax1.set_xlim(0.5, 1.5)
ax1.set_ylim(0, 3.22)


plt.tight_layout()
plt.show()

fig.savefig(
    config.app_config.plot_dir.joinpath(f"densities_grid_{day}.png"),
    transparent=True,
)
