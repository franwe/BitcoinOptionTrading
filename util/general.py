import pandas as pd
import numpy as np
from typing import Tuple, List

from datetime import datetime, timedelta


def create_dates(start: str, end: str, mode: str = "daily") -> List:
    if mode == "daily":
        dates = pd.date_range(start, end, closed="right", freq="D")
    elif mode == "weekly":
        dates = pd.date_range(
            start,
            end,
            closed="right",
            freq=pd.offsets.WeekOfMonth(week=1, weekday=2),
        )
    return [str(date.date()) for date in dates]


def load_tau_section_parameters(tau_section: str) -> Tuple[str, float, float, int, int]:
    """Load parameters for trading algorithm. Depending on tau section:

    Args:
        tau_section (str): small: 8-40, big: 41-99, huge: 100-182

    Returns:
        many: filename, near_bound, far_bound, tau_min, tau_max
    """
    if tau_section == "small":
        return "trades_smallTau.csv", 0.1, 0.3, 7, 40
    elif tau_section == "big":
        return "trades_bigTau.csv", 0.125, 0.35, 40, 99
    else:  # tau_section == "huge":
        return "trades_hugeTau.csv", 0.15, 0.4, 99, 183


def add_days(daystr: str, days: int) -> str:
    dt = datetime.strptime(daystr, "%Y-%m-%d")  # type: datetime
    dt_p = dt + timedelta(days=days)  # type: datetime
    future = dt_p.strftime("%Y-%m-%d")  # type: str
    return future


def sort_values_by_X(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    df = pd.DataFrame(y, X)
    df = df.sort_index()
    X_sorted = np.array(df.index)
    y_sorted = np.array(df[0])
    return X_sorted, y_sorted
