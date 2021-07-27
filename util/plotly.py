import os
from os.path import join
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from util.data import load_trades
from util.general import add_days

cwd = os.getcwd() + os.sep
source_data = join(cwd, "data", "00-raw") + os.sep
trade_data_directory = join(cwd, "data", "03-1_trades") + os.sep

trade_data_directory
day = "2020-03-18"
tau_day = 9
trade_type = "K2"
x = 0.5


def translate_color(c):
    if c == "red":
        return "rgb(255,0,0)"
    elif c == "blue":
        return "rgb(0,0,255)"


def plotly_plot(trading_day, trading_tau, trade_type, x=0.5):
    day = add_days(trading_day, -1)
    tau_day = trading_tau + 1
    execution_day = add_days(trading_day, trading_tau)

    data = load_trades(trading_day=trading_day, trading_tau=trading_tau, trade=trade_type)
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

    # Build figure
    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=(f"Densities {day}", f"Kernel {trading_day}", f"Payoff Diagram {execution_day}"),
    )

    # --------------------------------------------------------------- Densities
    colors = rnd_points.color.apply(lambda c: translate_color(c)).tolist()
    fig.add_trace(
        go.Scatter(
            x=rnd_points.M,
            y=rnd_points.q_M,
            mode="markers",
            name="options",
            opacity=0.4,
            marker=dict(
                size=7,
                symbol="circle",
                color=colors,
            ),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=M,
            y=rnd,
            mode="lines",
            line=dict(color="rgb(255,0,0)"),
            name="rnd",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=M, y=hd, mode="lines", line=dict(color="rgb(0,0,255)"), name="hd"),
        row=1,
        col=1,
    )

    # ------------------------------------------------------------- Kernel Plot
    fig.add_trace(  # K_bound
        go.Scatter(
            x=[1 - x, 1 - x, 1 + x, 1 + x],
            y=[1 - K_bound, 1 + K_bound, 1 + K_bound, 1 - K_bound],
            fill="toself",
            mode="lines",
            fillcolor="rgba(192,192,192,0.2)",
            line=dict(color="#0061ff", width=0),
        ),
        row=1,
        col=2,
    )
    for interval in M_bounds_buy:
        left = interval[0]
        right = interval[1]
        fig.add_trace(  # buy_areas
            go.Scatter(
                x=[left, left, right, right],
                y=[0, 2, 2, 0],
                fill="toself",
                mode="lines",
                fillcolor="rgba(255,0,0,0.1)",
                line=dict(color="#0061ff", width=0),
            ),
            row=1,
            col=2,
        )

    for interval in M_bounds_sell:
        left = interval[0]
        right = interval[1]
        fig.add_trace(  # sell_areas
            go.Scatter(
                x=[left, left, right, right],
                y=[0, 2, 2, 0],
                fill="toself",
                mode="lines",
                fillcolor="rgba(0,0,255,0.1)",
                line=dict(color="#0061ff", width=0),
            ),
            row=1,
            col=2,
        )

    fig.add_trace(  # kernel
        go.Scatter(
            x=M,
            y=kernel,
            mode="lines",
            line=dict(color="black"),
            name="kernel",
        ),
        row=1,
        col=2,
    )

    colors = df_all.color.apply(lambda c: translate_color(c)).tolist()
    fig.add_trace(  # available options
        go.Scatter(
            x=df_all.M,
            y=[1] * len(df_all.M),
            mode="markers",
            name="options",
            opacity=0.4,
            marker=dict(
                size=7,
                symbol="circle",
                color=colors,
            ),
        ),
        row=1,
        col=2,
    )
    S0 = df_all.S.mean()
    ST = df_all.ST.iloc[0]
    lower_S = min(S0 * 0.5, ST * 0.9)
    upper_S = max(S0 * 1.5, ST * 1.1)

    if df_trades is not None:
        colors = df_trades.color.apply(lambda c: translate_color(c)).tolist()
        fig.add_trace(  # trades
            go.Scatter(
                x=df_trades.M,
                y=[1] * len(df_trades.M),
                mode="markers",
                name="options",
                opacity=1,
                marker=dict(
                    size=10,
                    symbol="circle",
                    color=colors,
                ),
            ),
            row=1,
            col=2,
        )

        # ------------------------------------------------------------- Payoffs
        S = np.linspace(lower_S, upper_S, 200)

        # ST = df_trades.ST.iloc[0]
        fig.add_shape(
            type="line",
            x0=1,
            y0=-0.1,
            x1=S0,
            y1=0.1,
            line=dict(color="RoyalBlue", width=3),
            opacity=0.01,
            row=1,
            col=3,
        )
        fig.add_vline(
            x=ST,
            line_color="red",
            line_dash="dot",
            row="all",
            col=3,
            annotation_text="ST",
            opacity=0.25,
        )

        fig.add_vline(
            x=S0,
            line_color="grey",
            line_dash="dot",
            row="all",
            col=3,
            annotation_text="S0",
            opacity=0.25,
        )

        colors = df_trades.color.apply(lambda c: translate_color(c)).tolist()
        total = np.zeros(len(df_trades.payoffs.iloc[0]["payoff"]))
        for payoff, action in zip(df_trades.payoffs, df_trades.action):
            # single payoffs
            if action == "buy":
                fig.add_trace(
                    go.Scatter(
                        x=payoff["S"],
                        y=payoff["payoff"],
                        mode="lines",
                        line=dict(color="rgb(255,0,0)"),
                        opacity=0.4,
                    ),
                    row=1,
                    col=3,
                )
            if action == "sell":
                fig.add_trace(
                    go.Scatter(
                        x=payoff["S"],
                        y=payoff["payoff"],
                        mode="lines",
                        line=dict(color="rgb(0,0,255)"),
                        opacity=0.4,
                    ),
                    row=1,
                    col=3,
                )
            total += np.array(payoff["payoff"])
        total_payoff = {"S": payoff["S"], "payoff": total}

        fig.add_trace(  # total payoff
            go.Scatter(
                x=total_payoff["S"],
                y=total_payoff["payoff"],
                mode="lines",
                line=dict(color="black", width=4),
                name="total payoff",
            ),
            row=1,
            col=3,
        )

    # fig.update_yaxes(rangemode="nonnegative")
    # fig.update_xaxes(range=[1 - x, 1 + x])
    fig.update_layout(showlegend=False)
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(title_text="Moneyness", range=[1 - x, 1 + x], row=1, col=1)
    fig.update_xaxes(title_text="Moneyness", range=[1 - x, 1 + x], row=1, col=2)

    fig.update_xaxes(
        title_text="BTCUSD",
        range=[lower_S, upper_S],
        row=1,
        col=3,
    )
    fig.update_yaxes(title_text="USD", row=1, col=3)

    fig.update_yaxes(title_text=" ", rangemode="nonnegative", row=1, col=1)
    fig.update_yaxes(title_text=" ", range=[0, 2], row=1, col=2)
    fig.update_layout(
        template="none",
        height=400,
        width=1000,
        title_text="{}    {}    {}".format(day, tau_day, trade_type),
    )

    return fig


# fig = plotly_plot(trade_data_directory, day, tau_day, trade_type)
# fig.show()
