from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

import numpy as np
from matplotlib import pyplot as plt
from localpoly.base import LocalPolynomialRegression

from util.data import RndData
from util.configcore import config
from util.general import sort_values_by_X


def plot_locpoly_weights(X, y, x_points, h_1, h_2, kernel="gaussian"):

    X, y = sort_values_by_X(X, y)

    fig, (ax0, ax1) = plt.subplots(
        2,
        1,
        sharex=True,
        gridspec_kw={"height_ratios": [4, 1]},
        figsize=(4, 4),  # widht, hight
    )
    # density points
    y_density = np.zeros(X.shape[0])
    for i, x in enumerate(X):
        y_density[i] = np.random.uniform(0, 1)

    ax1.scatter(X, y_density, c="k", alpha=0.5)
    ax1.tick_params(
        axis="y",  # changes apply to the y-axis
        which="both",  # both major and minor ticks are affected
        left=False,  # ticks along the bottom edge are off
        right=False,  # ticks along the top edge are off
        labelleft=False,  # labels along the bottom edge are off)
    )
    ax1.set_xlabel("Moneyness")
    ax0.set_ylabel(r"Weight $W_i$")

    # weights
    for x, c in zip(x_points, ["#1f77b4", "#ff7f0e", "#2ca02c"]):
        model_1 = LocalPolynomialRegression(
            X=X, y=y, h=h_1, kernel=kernel, gridsize=100
        )
        results_1 = model_1.localpoly(x)
        model_2 = LocalPolynomialRegression(
            X=X, y=y, h=h_2, kernel=kernel, gridsize=100
        )
        results_2 = model_2.localpoly(x)
        ax0.plot(X, results_1["weight"], c=c)
        ax0.plot(X, results_2["weight"], ls=":", c=c)

    plt.tight_layout()
    return fig


# -------------------------------------------------------------------- SETTINGS
day = "2020-03-11"
tau_day = 9
x_points = [0.85, 1, 1.15]
h1 = 0.074

RndData = RndData(cutoff=config.model_config.cutoff)
df_tau = RndData.filter_data(date=day, tau_day=tau_day, mode="unique")

X = np.array(df_tau.M)
y = np.array(df_tau.iv)

h2 = h1 / 2
fig_weights = plot_locpoly_weights(X, y, x_points, h1, h2, kernel="gaussian")
plt.show()

fig_weights.savefig(
    config.app_config.plot_dir.joinpath(f"Locpoly_Weights_{day}.png"),
    transparent=True,
)
