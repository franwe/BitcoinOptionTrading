from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

import numpy as np
from matplotlib import pyplot as plt

from localpoly.base import LocalPolynomialRegressionCV
from spd_trading import risk_neutral_density as rnd

from util.data import RndData
from util.configcore import config

# -------------------------------------------------------------------- SETTINGS
day = "2020-03-11"
tau_day = 9

RndData = RndData(cutoff=config.model_config.cutoff)
df_tau = RndData.filter_data(date=day, tau_day=tau_day, mode="unique")

X = np.array(df_tau.M)
y = np.array(df_tau.iv)

# --------------------------------------------------------- FIND MINIMAL MSE x2
list_of_bandwidths, bw_silver, lower_bound = rnd.create_bandwidth_range(X)
model_cv = LocalPolynomialRegressionCV(
    X=X,
    y=y,
    kernel="gaussian",
    n_sections=15,
    loss="MSE",
    sampling="slicing",
)
results = model_cv.bandwidth_cv(list_of_bandwidths)

print(f"Optimal Bandwidth: {results['fine results']['h']}")
# ------------------------------------------------------------------------ PLOT
fig, ax = plt.subplots(1, 1, figsize=(4, 4))
ax.plot(results["coarse results"]["bandwidths"], results["coarse results"]["MSE"], ":", c="k")
ax.plot(results["fine results"]["bandwidths"], results["fine results"]["MSE"], "-", c="k")
ax.set_xlabel("bandwidth")
ax.set_ylabel("MSE")
ax.set_xlim(0.048, 0.092)
ax.set_ylim(0.000645, 0.000914)
ax.set_yticks([])
plt.tight_layout()
plt.show()

fig.savefig(config.app_config.plot_dir.joinpath("bandwidth_MSE.png"), transparent=True)
