from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

import numpy as np
from matplotlib import pyplot as plt
from statsmodels.api import qqplot

from spd_trading import historical_density as hd
from util.configcore import config
from util.data import HdData

tau_day = 50


def get_HD_model(day, tau_day):
    hd_data, S0_binance = HdData.filter_data(day)
    S0 = HdData.get_S0(day)
    HD = hd.Calculator(
        data=hd_data,
        tau_day=tau_day,
        date=day,
        S0=S0,
        garch_data_folder=config.app_config.data_garch,
        n_fits=config.model_config.n_fits,
        cutoff=config.model_config.cutoff,
        overwrite_model=False,
        overwrite_simulations=False,
        window_length=config.model_config.window_length,
        simulations=config.model_config.simulations,
    )
    HD.get_hd(variate_GARCH_parameters=True)
    return HD


# -------------------------------------------------------------------- QQ-PLOTS
def create_garch_qq(HD):
    z = HD.GARCH.z_process
    qq_fig = qqplot(np.array(z), line="45", markersize=3, markerfacecolor="k")
    return qq_fig


HdData = HdData()
dates = ["2020-03-05", "2020-09-26"]
for day in dates:
    HD = get_HD_model(day, tau_day)

    qq_fig = create_garch_qq(HD)
    ax = qq_fig.axes[0]
    ax.set_aspect("equal", "box")
    qq_fig.set_size_inches(4, 4)

    qq_fig.savefig(config.app_config.plot_dir.joinpath(f"GARCH_qq_{day}.png"), transparent=True)

plt.show()

# ------------------------------------------------------------------ PARAMETERS


def substract_offset(x, offset=205):
    return x - offset


def add_offset(x, offset=205):
    return x + offset


HD_1 = get_HD_model(dates[0], tau_day)
HD_2 = get_HD_model(dates[1], tau_day)
n = config.model_config.n_fits
X_1 = np.linspace(1, n, n)
delta = 205
X_2 = np.linspace(1 + delta, n + delta, n)

fig_pars, axes = plt.subplots(4, 1, figsize=(8, 4), sharex=True)
fig_pars.subplots_adjust(hspace=0)

for pars, X, color, ls in zip(
    [HD_1.GARCH.parameters, HD_2.GARCH.parameters],
    [X_1, X_2],
    ["r", "b"],
    ["-", "--"],
):
    for i, name in zip(range(0, 3), [r"$\omega$", r"$\alpha$", r"$\beta$"]):
        axes[i].plot(X, pars[:, i + 1], c=color, ls=ls)
        axes[i].set_ylabel(name)
    axes[3].plot(X, pars[:, 2] + pars[:, 3], c=color, ls=ls)
    axes[3].set_ylabel(r"$\alpha + \beta$")
axes[3].set_xlabel("moving windows towards 2020-03-05")
labels_1 = ["", "0", "100", "200", "300", "400", "", "", ""]
axes[3].set_xticklabels(labels_1)
axes[3].tick_params(axis="x", colors="red")
axes[3].xaxis.label.set_color("red")

secax = axes[0].secondary_xaxis("top", functions=(substract_offset, add_offset))
secax.set_xlabel("moving windows towards 2020-09-26")
labels_2 = ["", "", "", "0", "100", "200", "300", "400", ""]
secax.set_xticklabels(labels_2)
secax.tick_params(axis="x", colors="blue")
secax.xaxis.label.set_color("blue")

plt.tight_layout()
plt.show()

fig_pars.savefig(config.app_config.plot_dir.joinpath("GARCH_pars.png"), transparent=True)
