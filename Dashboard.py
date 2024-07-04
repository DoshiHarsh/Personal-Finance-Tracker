import streamlit as st
from core_components.database import ConnectDB
from core_components.functions import Currencies
import pandas as pd
from babel.numbers import format_currency
import plotly.express as px
from datetime import datetime, timedelta

db_operations = ConnectDB("budget_db")
curr = Currencies(db_operations)
base_currency = curr.get_base_currency()
today = datetime.today()

st.set_page_config(
    page_title="Budget tracking",
    layout="wide",
    initial_sidebar_state="expanded",
)


def check_database_setup():
    tables_check = [
        "event_logs",
        "categories",
        "currencies",
        "currency_rates",
        "accounts",
        "account_types",
        "cashflow_transactions",
        "cashflow_transfers",
        "rewards_accounts",
        "rewards_categories",
    ]
    views_check = [
        "detailed_accounts",
        "detailed_transactions",
        "detailed_transfers",
        "detailed_reward_accounts",
    ]
    for table in tables_check:
        db_operations.table_create_if_missing(table)
    for view in views_check:
        db_operations.create_table_view(view)
    curr.check_and_update_currency_rates()
    st.session_state["initial_db_check"] = "Complete"


@st.cache_data(show_spinner=True)
def get_database_tables(table_list):
    for table in table_list:
        st.session_state[f"{table}_df"] = db_operations.table_query(
            f"Select * from {table}"
        )


def filter_df(df_name, **kwargs):
    df = st.session_state[df_name]
    if df_name == "detailed_transactions_df":
        cols = {
            "account_types_filter": "transaction_account_type_name",
            "accounts_filter": "transaction_account_name",
            "categories_types_filter": "transaction_category_name",
            "date_filter": "transaction_date",
            "transaction_status_filter": "transaction_status",
            "transfers_filter": "transaction_merchant_name",
            "inflow_filter": "transaction_amount",
            "cumulative_calculation": "transaction_amount",
        }
    if "account_types_filter" in kwargs.keys():
        if len(kwargs["account_types_filter"]) > 0:
            df = df[
                df[cols["account_types_filter"]].isin(kwargs["account_types_filter"])
            ]
    if "accounts_filter" in kwargs.keys():
        if len(kwargs["accounts_filter"]) > 0:
            df = df[df[cols["accounts_filter"]].isin(kwargs["accounts_filter"])]
    if "categories_types_filter" in kwargs.keys():
        if len(kwargs["categories_types_filter"]) > 0:
            df = df[
                df[cols["categories_types_filter"]].isin(
                    kwargs["categories_types_filter"]
                )
            ]
    if "date_filter" in kwargs.keys():
        df = df[
            pd.to_datetime(df[cols["date_filter"]]).between(
                kwargs["date_filter"][0], kwargs["date_filter"][1]
            )
        ]
    if "transaction_status_filter" in kwargs.keys():
        if kwargs["transaction_status_filter"] == "Completed Only":
            df = df[df[cols["transaction_status_filter"]] != "Pending"]
    if "transfers_filter" in kwargs.keys():
        if kwargs["transfers_filter"]:
            df = df[~df[cols["transfers_filter"]].astype(str).str.contains("Transfer")]
    if "inflow_filter" in kwargs.keys():
        if kwargs["inflow_filter"]:
            df = df[((df[cols["inflow_filter"]] > 0))]
    if "cumulative_calculation" in kwargs.keys():
        if kwargs["cumulative_calculation"]:
            cumulative_calc = df.sort_values("transaction_date")[
                "transaction_amount"
            ].cumsum()
            df = df.join(cumulative_calc, rsuffix="_cumulative").sort_values(
                "transaction_date"
            )
            zero_val_df = pd.DataFrame(
                {
                    "transaction_date": [df["transaction_date"].min()],
                    "transaction_amount_cumulative": [0],
                    "transaction_amount": [0],
                }
            )
            df = pd.concat([zero_val_df, df])
    return df


def df_summary(df, groupby_cols, return_cols, type="sum"):
    if type == "sum":
        try:
            df = pd.DataFrame(df.groupby(groupby_cols).sum()[return_cols]).reset_index()
        except Exception as e:
            print(e)
            df = pd.DataFrame()
    return df


if "initial_db_check" not in st.session_state:
    check_database_setup()

get_database_tables(
    [
        "accounts",
        "account_types",
        "currencies",
        "currency_rates",
        "categories",
        "cashflow_transfers",
        "cashflow_transactions",
        "rewards_accounts",
        "detailed_accounts",
        "detailed_transactions",
        "detailed_transfers",
        "detailed_reward_accounts",
    ]
)

st.title("Personal Finances Dashboard")
dashboard_viz = st.container()

block1 = dashboard_viz.columns(5)
account_types_filter = block1[0].multiselect(
    label="Account Types",
    options=st.session_state["detailed_accounts_df"]["account_type_name"].unique(),
)
accounts_filter = block1[1].multiselect(
    label="Account Filters",
    options=st.session_state["detailed_accounts_df"]["account_name"].unique(),
)
date_filter = block1[2].selectbox(
    label="Date Range",
    options=["Current Month", "Last 30 Days", "Last 365 Days", "YTD", "Custom"],
)
if date_filter == "Custom":
    start_date_filter = pd.to_datetime(
        block1[1].date_input(label="Start Date", value="today")
    )
    end_date_filter = pd.to_datetime(
        block1[2].date_input(
            label="End Date", value="today", min_value=start_date_filter
        )
    )
elif date_filter == "Current Month":
    start_date_filter, end_date_filter = datetime(today.year, today.month, 1), datetime(
        today.year, today.month, 1
    ) + pd.offsets.MonthEnd(1)
elif date_filter == "Last 30 Days":
    start_date_filter, end_date_filter = today - timedelta(30), today
elif date_filter == "Last 365 Days":
    start_date_filter, end_date_filter = today - timedelta(365), today
elif date_filter == "YTD":
    start_date_filter, end_date_filter = datetime(today.year, 1, 1), today
categories_types_filter = block1[3].multiselect(
    label="Categories",
    options=st.session_state["detailed_transactions_df"][
        "transaction_category_name"
    ].unique(),
)
transaction_status_filter = block1[4].selectbox(
    label="Transaction Status",
    options=["Completed Only", "Complete + Pending"],
    index=0,
)
filter_args = {
    "account_types_filter": account_types_filter,
    "accounts_filter": accounts_filter,
    "date_filter": (start_date_filter, end_date_filter),
    "categories_types_filter": categories_types_filter,
    "transaction_status_filter": transaction_status_filter,
    "transfers_filter": False,
    "inflow_filter": False,
    "cumulative_calculation": False,
}

block2 = dashboard_viz.columns([8, 2])
block2[0].subheader("Spend Path")
spend_path_args = filter_args
sub_block2 = block2[0].columns(3)
include_transfers = sub_block2[0].checkbox(label="Include Transfers")
include_inflow = sub_block2[1].checkbox(label="Include Income")
if not include_transfers:
    spend_path_args["transfers_filter"] = True
if not include_inflow:
    spend_path_args["inflow_filter"] = True
spend_path_args["cumulative_calculation"] = True
spend_path_df = filter_df(df_name="detailed_transactions_df", **spend_path_args)
spend_path_df["transaction_amount"] = spend_path_df["transaction_amount"].apply(
    lambda x: format_currency(x, base_currency)
)
spend_path_df["transaction_amount_cumulative"] = spend_path_df[
    "transaction_amount_cumulative"
].apply(lambda x: format_currency(x, base_currency))
spend_path_fig = px.line(
    spend_path_df,
    x="transaction_date",
    y="transaction_amount_cumulative",
    markers=True,
    line_shape="linear",
)
spend_path_fig.update_traces(
    text=spend_path_df[["transaction_amount", "transaction_amount_cumulative"]],
    customdata=spend_path_df["transaction_merchant_name"],
    hovertemplate="<b>%{customdata}</b>"
    + "<br><b>Transaction Amount:</b> %{text[1]}</br>"
    + "<b>Cumulative Total:</b> %{text[0]}"
    + "<br><b>Transaction Date:</b> %{x}</br>",
)
spend_path_fig.update_layout(
    hoverlabel=dict(bgcolor="#0E1117", font_size=16, font_family="Sans Serif"),
    xaxis_range=[start_date_filter - timedelta(1), end_date_filter + timedelta(1)],
)
block2[0].plotly_chart(spend_path_fig, use_container_width=True)

block2[1].subheader("Current Balances")
container2 = block2[1].container(height=400)
current_balances_args = {
    k: filter_args[k]
    for k in ["account_types_filter", "date_filter"]
    if k in filter_args
}
current_balances_df = filter_df(
    df_name="detailed_transactions_df", **current_balances_args
)
account_total = df_summary(
    current_balances_df, "transaction_account_id", "transaction_amount"
)
for index, row in (
    st.session_state["detailed_accounts_df"]
    .sort_values(["account_type_name", "account_name"])
    .iterrows()
):
    try:
        transactions_sum = account_total.loc[
            account_total["transaction_account_id"] == row["account_id"],
            "transaction_amount",
        ].iloc[0]
    except Exception:
        transactions_sum = 0
    current_balance = format_currency(
        row["account_starting_balance"] - transactions_sum,
        row["account_currency"],
        locale="en_US",
    )
    balance_delta = format_currency(
        -transactions_sum, row["account_currency"], locale="en_US"
    )
    container2.metric(
        label=f"{row["account_name"]} :gray-background[:blue[{row["account_type_name"]}]]",
        value=current_balance,
        delta=balance_delta,
    )

block3 = dashboard_viz.columns(2)
category_spend_args = {
    k: filter_args[k]
    for k in [
        "account_types_filter",
        "accounts_filter",
        "transaction_status_filter" "transfers_filter",
        "inflow_filter",
        "date_filter",
        "cumulative_calculation",
    ]
    if k in filter_args
}
if not include_transfers:
    spend_path_args["inflow_filter"] = True
category_spend_args["transfers_filter"] = True
category_spend_df = filter_df(df_name="detailed_transactions_df", **category_spend_args)
category_spend_fig = px.bar(
    category_spend_df, "transaction_category_name", "transaction_amount"
)
category_spend_fig.update_layout(
    hoverlabel=dict(bgcolor="#0E1117", font_size=16, font_family="Sans Serif")
)
block3[0].plotly_chart(category_spend_fig, use_container_width=True)
