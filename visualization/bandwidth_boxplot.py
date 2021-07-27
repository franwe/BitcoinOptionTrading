from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from matplotlib import pyplot as plt
import pandas as pd

from util.configcore import config

# ------------------------------------------------------------------------ MAIN

# correction to boxplot mean +/- std get median
bw = pd.read_csv(config.app_config.bandwidths_table)
bw_2 = pd.read_csv(config.app_config.bandwidths_table)


def replace_by_median(value, describe):
    if (value > describe["mean"] + describe["std"]) or (value < describe["mean"] - describe["std"]):
        value = describe["50%"]
    return value


def replace_by_bound(value, describe):
    if value > describe["75%"]:
        value = describe["75%"]
    elif value < describe["25%"]:
        value = describe["25%"]
    return value


def replace_lower(value, describe):
    if value < describe["25%"]:
        value = describe["50%"]
    return value


cols = ["h_m", "h_m2"]
for col in cols:
    desc_stat = bw_2[col].describe()
    print(desc_stat)
    bw[col] = bw_2[col].apply(lambda val: replace_by_bound(val, desc_stat))
    del desc_stat

col = "h_k"
desc_stat = bw_2[col].describe()
print(desc_stat)
bw[col] = bw_2[col].apply(lambda val: replace_lower(val, desc_stat))

# -------------------- boxplot
fig, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=(4, 4))
outliers = dict(markeredgecolor="k", marker=".")
ax0.boxplot(
    bw_2.h_m,
    labels=[
        r"""$h_{smile}$
(Moneyness)"""
    ],
    flierprops=outliers,
    widths=(0.5),
    medianprops=dict(color="grey")
)
ax0.set_ylim(-0.15, 1.2)
ax1.boxplot(
    bw_2.h_m2,
    labels=[
        r"""$h_{RND,M}$
(Moneyness)"""
    ],
    flierprops=outliers,
    widths=(0.5),
    medianprops=dict(color="grey")
)
ax1.set_ylim(-0.15, 1.2)
ax2.boxplot(
    bw_2.h_k,
    labels=[
        r"""$h_{RND,K}$
(Strike Price)"""
    ],
    flierprops=outliers,
    widths=(0.5),
    medianprops=dict(color="grey")
)
ax2.set_ylim(-450, 3600)

plt.tight_layout()
plt.show()

fig.savefig(config.app_config.plot_dir.joinpath("bandwidth_boxplot_k15n30.png"), transparent=True)
