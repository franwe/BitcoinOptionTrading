import dash
from dash.dependencies import Input, Output
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

from util.plotly import plotly_plot
from util.general import add_days
from util.configcore import config


df = pd.read_csv(config.app_config.data_trades.joinpath("trades.csv"))
print(config.app_config.data_trades)

df["id"] = range(0, df.shape[0])
df.set_index("id", inplace=True, drop=False)
df["maturity"] = df.apply(lambda row: add_days(row.date, row.tau_day), axis=1)


def evaluate(dff):
    all = dff[["total", "t0_payoff", "T_payoff"]].sum()
    all["trade"] = "all"
    all["count"] = dff.shape[0]
    trades = (dff[["total", "t0_payoff", "T_payoff", "trade"]].groupby(by="trade").sum()).reset_index()
    trades_count = (dff[["trade", "total"]].groupby(by="trade").count()).reset_index()
    trades_count.columns = ["trade", "count"]
    trades = trades.merge(trades_count)

    all = pd.DataFrame(all).transpose()
    evaluated_values = all.append(trades)

    return evaluated_values[["trade", "count", "total", "t0_payoff", "T_payoff"]].to_dict("records")


df_evaluate = pd.DataFrame(evaluate(df))

app = dash.Dash(__name__)

styles = {"pre": {"border": "thin lightgrey solid", "overflowX": "scroll"}}
application = app.server

app.layout = html.Div(
    [
        dcc.Graph(id="plot"),
        dash_table.DataTable(
            id="datatable-row-ids",
            columns=[{"name": i, "id": i, "deletable": False, "selectable": False} for i in df.columns],
            data=df.to_dict("records"),
            filter_action="custom",
            filter_query="",
            sort_action="native",
            sort_mode="multi",
            hidden_columns=["id", "Unnamed: 0"],
            row_selectable="single",
            row_deletable=False,
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=10,
            css=[{"selector": ".show-hide", "rule": "display: none"}],
        ),
        dcc.Markdown(""" ## Aggregation Table """),
        dash_table.DataTable(
            id="datatable-aggregate",
            columns=[{"name": i, "id": i, "deletable": False, "selectable": False} for i in df_evaluate.columns],
            data=df.to_dict("records"),
            editable=False,
            sort_action="native",
            sort_mode="multi",
            row_deletable=False,
            page_action="native",
            page_current=0,
            page_size=10,
        ),
        html.Div(id="datatable-row-ids-container"),
    ]
)


operators = [
    ["ge ", ">="],
    ["le ", "<="],
    ["lt ", "<"],
    ["gt ", ">"],
    ["ne ", "!="],
    ["eq ", "="],
    ["contains "],
    ["datestartswith "],
]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find("{") + 1 : name_part.rfind("}")]

                value_part = value_part.strip()
                v0 = value_part[0]
                if v0 == value_part[-1] and v0 in ("'", '"', "`"):
                    value = value_part[1:-1].replace("\\" + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


@app.callback(
    [
        Output("datatable-row-ids", "data"),
        Output("datatable-aggregate", "data"),
    ],
    [Input("datatable-row-ids", "filter_query")],
)
def update_table(filter):
    filtering_expressions = filter.split(" && ")
    dff = df
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ("eq", "ne", "lt", "le", "gt", "ge"):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == "contains":
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == "datestartswith":
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    data_evaluation = evaluate(dff)

    return dff.to_dict("records"), data_evaluation


@app.callback(
    Output("datatable-row-ids", "page_current"),
    [Input("datatable-row-ids", "filter_query")],
)
def reset_to_page_0(filter_query):
    return 0


@app.callback(
    Output("datatable-row-ids-container", "children"),
    [
        Input("datatable-row-ids", "derived_virtual_row_ids"),
        Input("datatable-row-ids", "selected_row_ids"),
        Input("datatable-row-ids", "active_cell"),
    ],
)
def update_graphs(row_ids, selected_row_ids, active_cell):
    # When the table is first rendered, `derived_virtual_data` and
    # `derived_virtual_selected_rows` will be `None`. This is due to an
    # idiosyncrasy in Dash (unsupplied properties are always None and Dash
    # calls the dependent callbacks when the component is first rendered).
    # So, if `rows` is `None`, then the component was just rendered
    # and its value will be the same as the component's dataframe.
    # Instead of setting `None` in here, you could also set
    # `derived_virtual_data=df.to_rows('dict')` when you initialize
    # the component.
    selected_id_set = set(selected_row_ids or [])

    print(selected_row_ids)

    if row_ids is None:
        dff = df
        # pandas Series works enough like a list for this to be OK
        row_ids = df["id"]
    else:
        dff = df.loc[row_ids]

    active_row_id = active_cell["row_id"] if active_cell else None

    colors = ["#FF69B4" if id == active_row_id else "#7FDBFF" if id in selected_id_set else "#0074D9" for id in row_ids]

    return [
        dcc.Graph(
            id=column + "--row-ids",
            figure={
                "data": [
                    {
                        "x": dff["date"],
                        "y": dff[column],
                        "type": "bar",
                        "marker": {"color": colors},
                    }
                ],
                "layout": {
                    "xaxis": {"automargin": True},
                    "yaxis": {"automargin": True, "title": {"text": column}},
                    "height": 250,
                    "margin": {"t": 10, "l": 10, "r": 10},
                },
            },
        )
        # check if column exists - user may have deleted it
        # If `column.deletable=False`, then you don't
        # need to do this check.
        for column in ["total", "t0_payoff", "T_payoff"]
        if column in dff
    ]


@app.callback(
    dash.dependencies.Output("plot", "figure"),
    [
        Input("datatable-row-ids", "derived_virtual_row_ids"),
        Input("datatable-row-ids", "selected_row_ids"),
        Input("datatable-row-ids", "active_cell"),
    ],
)
def update_plot(row_ids, selected_row_ids, active_cell):

    if row_ids is None:
        dff = df
        row_ids = df["id"]
    else:
        dff = df.loc[row_ids]

    i = selected_row_ids[0] if selected_row_ids else dff.id.tolist()[0]
    day = df.loc[i, "date"]
    tau_day = int(df.loc[i, "tau_day"])
    trade_type = df.loc[i, "trade"]

    fig = plotly_plot(day, tau_day, trade_type)
    return fig


if __name__ == "__main__":
    app.run_server(debug=False)
