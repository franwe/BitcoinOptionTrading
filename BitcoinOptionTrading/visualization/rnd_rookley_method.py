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
x = 0.3

RndData = RndData(cutoff=config.model_config.cutoff)
df_tau = RndData.filter_data(date=day, tau_day=tau_day, mode="unique")

RND = rnd.Calculator(
    data=df_tau,
    tau_day=tau_day,
    date=day,
    sampling=config.model_config.sampling,
    n_sections=config.model_config.n_sections,
    loss=config.model_config.loss,
    kernel=config.model_config.kernel,
    overwrite_RND=False,
    data_folder=config.app_config.data_rnd,
    h_m=0.090,
    h_k=211.01,
    h_m2=0.041,
)
RND.get_rnd()

# algorithm plot
RndPlot = rnd.Plot(x)
fig_method = RndPlot.rookleyMethod(RND)

fig_method.savefig(
    config.app_config.plot_dir.joinpath(f"RND_T-{tau_day}_{day}.png"),
    transparent=True,
)
