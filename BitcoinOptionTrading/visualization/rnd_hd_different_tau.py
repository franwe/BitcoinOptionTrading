from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

import numpy as np
import pandas as pd
import os
from matplotlib import pyplot as plt
from matplotlib.pyplot import cm

from util.data import load_rnd_hd
from util.configcore import config

# ------------------------------------------------ RND HD DENSITIES FOR ONE DAY
day = "2020-09-02"


def strp_file(filename):
    tau_part, date_part = filename.split("_")
    _, tau = tau_part.split("-")
    date, _ = date_part.split(".")
    return pd.Series([date, int(tau)])


filepaths = config.app_config.data_densities.glob(f"*_{day}.pkl")
files = [str(filepath).split(os.sep)[-1] for filepath in filepaths]

df = pd.DataFrame(files, columns=["filename"])
df[["day", "tau_day"]] = df.filename.apply(lambda f: strp_file(f))

densities = df.sort_values(by="tau_day")
print("------- ", day, len(densities))

# ------------------------------------------------------------------------ PLOT
color = cm.rainbow(np.linspace(0, 1, len(densities)))
x_pos, y_pos = 0.99, 0.99
fig_hd, ax_hd = plt.subplots(1, 1, figsize=(4, 4))
fig_rnd, ax_rnd = plt.subplots(1, 1, figsize=(4, 4))
for (index, row), c in zip(densities.iterrows(), color):
    (RND, HD, Kernel) = load_rnd_hd(row.day, row.tau_day)
    ax_hd.plot(HD.q_M["x"], HD.q_M["y"], c=c)
    ax_hd.text(
        x_pos,
        y_pos,
        str(row.tau_day),
        horizontalalignment="right",
        verticalalignment="top",
        transform=ax_hd.transAxes,
        c=c,
    )
    ax_hd.set_xlabel("Moneyness")
    ax_hd.set_ylim(0)
    ax_hd.set_xlim(0.5, 1.5)

    ax_rnd.plot(RND.q_M["x"], RND.q_M["y"], c=c)
    ax_rnd.text(
        x_pos,
        y_pos,
        str(row.tau_day),
        horizontalalignment="right",
        verticalalignment="top",
        transform=ax_rnd.transAxes,
        c=c,
    )
    ax_rnd.set_xlabel("Moneyness")
    ax_rnd.set_ylim(0)
    ax_rnd.set_xlim(0.5, 1.5)
    y_pos -= 0.05

plt.tight_layout()
plt.show()

print("save to: ", config.app_config.plot_dir.joinpath(f"RND_{day}.png"))
fig_hd.savefig(config.app_config.plot_dir.joinpath(f"HD_{day}.png"), transparent=True)
fig_rnd.savefig(config.app_config.plot_dir.joinpath(f"RND_{day}.png"), transparent=True)
