from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

import math
from matplotlib import pyplot as plt
import numpy as np

from spd_trading import risk_neutral_density as rnd
from localpoly.base import LocalPolynomialRegressionCV

from util.data import RndData, load_rnd_hd
from util.configcore import config
from util.general import sort_values_by_X


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def get_slice(X, y, slice, no_slices=15):
    X, y = sort_values_by_X(X, y)
    n = X.shape[0]
    idx = list(range(0, n))
    slices = list(chunks(idx, math.ceil(n / no_slices)))
    return X[slices[slice]], y[slices[slice]]


RndData = RndData(cutoff=config.model_config.cutoff)
# ----------------------------------------------------- 2020-03-12 T=15 IV SMILE
day = "2020-03-12"
tau_day = 15
df_tau = RndData.filter_data(date=day, tau_day=tau_day, mode="unique")

X = np.array(df_tau.M)
y = np.array(df_tau.iv)
list_of_bandwidths, bw_silver, lower_bound = rnd.create_bandwidth_range(X)
model_slicing = LocalPolynomialRegressionCV(
    X=X,
    y=y,
    kernel="gaussian",
    n_sections=15,
    loss="MSE",
    sampling="slicing",
)
results_slicing = model_slicing.bandwidth_cv(list_of_bandwidths)
print(f"Optimal Bandwidth - slicing: {results_slicing['fine results']['h']}")
model_slicing.h = results_slicing["fine results"]["h"]
fit_slicing = model_slicing.fit(prediction_interval=(X.min(), X.max()))

model_random = LocalPolynomialRegressionCV(
    X=X,
    y=y,
    kernel="gaussian",
    n_sections=15,
    loss="MSE",
    sampling="random",
)
results_random = model_random.bandwidth_cv(list_of_bandwidths)
print(f"Optimal Bandwidth - random: {results_random['fine results']['h']}")
model_random.h = results_random["fine results"]["h"]
fit_random = model_random.fit(prediction_interval=(X.min(), X.max()))


fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(7, 3))

x_slice, y_slice = get_slice(X, y, 5)
ax0.scatter(df_tau.M, df_tau.iv, marker=".", s=1, c="r")
ax0.scatter(x_slice, y_slice, marker=".", s=1, c="blue")
ax0.plot(fit_slicing["X"], fit_slicing["fit"], "--", c="k", lw=1.5)
ax0.plot(fit_random["X"], fit_random["fit"], "-", c="k", lw=1)
ax0.set_xlabel("Moneyness")
ax0.set_ylabel("Implied Volatility")


# ---------------------------------------------------- 2020-04-19 T=12 - Density
day = "2020-04-19"
tau_day = 12
RND, HD, Kernel = load_rnd_hd(day, tau_day)

X = np.array(RND.data.M)
y = np.array(RND.data.q_M)
list_of_bandwidths, bw_silver, lower_bound = rnd.create_bandwidth_range(X)
model_slicing = LocalPolynomialRegressionCV(
    X=X,
    y=y,
    kernel="gaussian",
    n_sections=15,
    loss="MSE",
    sampling="slicing",
)
results_slicing = model_slicing.bandwidth_cv(list_of_bandwidths)
print(f"Optimal Bandwidth - slicing: {results_slicing['fine results']['h']}")
model_slicing.h = results_slicing["fine results"]["h"]
fit_slicing = model_slicing.fit(prediction_interval=(X.min(), X.max()))

model_random = LocalPolynomialRegressionCV(
    X=X,
    y=y,
    kernel="gaussian",
    n_sections=15,
    loss="MSE",
    sampling="random",
)
results_random = model_random.bandwidth_cv(list_of_bandwidths)
print(f"Optimal Bandwidth - random: {results_random['fine results']['h']}")
model_random.h = results_random["fine results"]["h"]
fit_random = model_random.fit(prediction_interval=(X.min(), X.max()))


x_slice, y_slice = get_slice(X, y, 10)
ax1.scatter(RND.data.M, RND.data.q_M, marker=".", c="r", s=70)
ax1.scatter(x_slice, y_slice, marker=".", c="blue", s=70)
ax1.plot(fit_slicing["X"], fit_slicing["fit"], "--", c="k", lw=1.5)
ax1.plot(fit_random["X"], fit_random["fit"], "-", c="k", lw=1)
ax1.set_xlabel("Moneyness")
ax1.set_ylabel("Risk Neutral Density")

plt.tight_layout()
plt.show()

fig.savefig(config.app_config.plot_dir.joinpath("bandwidth_slicing.png"), transparent=True)
