import streamlit as st
from core_components.functions import (
    curr,
    display_filter_ui,
    db_operations,
    df_summary,
    filter_df,
    filterArgs,
    get_current_account_balances,
)
from babel.numbers import format_currency
import plotly.express as px
from datetime import timedelta


st.set_page_config(
    page_title="Budget tracking",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "initial_db_check" not in st.session_state:
    for table in [
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
    ]:
        if not db_operations.table_exists(table):
            db_operations.table_create(table)
            db_operations.create_table_trigger(table)
            db_operations.insert_initial_values(table)
    for view in [
        "detailed_accounts",
        "detailed_transactions",
        "detailed_transfers",
        "detailed_rewards_accounts",
    ]:
        db_operations.create_table_view(view)
    curr.check_and_update_currency_rates()
    st.session_state["initial_db_check"] = "Complete"

for table in [
    "account_types",
    "currencies",
    "currency_rates",
    "categories",
    "detailed_accounts",
    "detailed_transactions",
    "detailed_transfers",
    "detailed_rewards_accounts",
]:
    if f"{table}_df" not in st.session_state:
        st.session_state[f"{table}_df"] = db_operations.table_query(
            f"Select * from {table}"
        )

st.session_state["current_account_balances_df"] = get_current_account_balances(
    st.session_state["detailed_transactions_df"],
    st.session_state["detailed_accounts_df"],
)
base_currency = curr.get_base_currency()
st.title("Personal Finances Dashboard")
filter_args = display_filter_ui(type="transaction_filters")
dashboard_viz = st.container()
block1 = dashboard_viz.columns([8, 3])
block2 = dashboard_viz.columns(2)

# Spend Path viz
with block1[0]:
    st.subheader("Spend Path", anchor=False)
    spend_path_args = filter_args
    spend_path_args["cumulative_calculation"] = True

    spend_path_df = filter_df(df_name="detailed_transactions_df", **spend_path_args)
    spend_path_df["transaction_amount"] = spend_path_df["transaction_amount"].apply(
        lambda x: format_currency(x, base_currency)
    )
    spend_path_df["transaction_amount_cumulative_display"] = spend_path_df[
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
        text=spend_path_df[
            [
                "transaction_merchant_name",
                "transaction_amount",
                "transaction_amount_cumulative_display",
            ]
        ],
        hovertemplate="<b>%{text[0]}</b>"
        + "<br><b>Transaction Amount:</b> %{text[1]}</br>"
        + "<b>Cumulative Total:</b> %{text[2]}"
        + "<br><b>Transaction Date:</b> %{x}</br>",
    )
    spend_path_fig.update_layout(
        hoverlabel=dict(bgcolor="#0E1117", font_size=16, font_family="Sans Serif"),
        xaxis_range=[
            filter_args["date_filter"][0] - timedelta(1),
            filter_args["date_filter"][1] + timedelta(1),
        ],
    )
    st.plotly_chart(spend_path_fig, use_container_width=True)

# Current Account Balances viz
with block1[1]:
    st.subheader("Current Balances", anchor=False)
    con = st.container(height=400)
    current_balances_args: filterArgs = {
        k: filter_args[k] for k in ["date_filter"] if k in filter_args
    }
    
    filtered_transactions_df = filter_df(
        df_name="detailed_transactions_df", **current_balances_args
    )
    delta_total = df_summary(
        filtered_transactions_df,
        "transaction_account_id",
        "transaction_amount",
        "delta_transaction_amount",
    )
    balance_viz_df = st.session_state["current_account_balances_df"].merge(
        delta_total, left_on="account_id", right_on="transaction_account_id", how="left"
    )
    balance_viz_df["delta_transaction_amount"] = balance_viz_df[
        "delta_transaction_amount"
    ].fillna(0.00)

    for index, row in balance_viz_df.sort_values(
        ["account_type_name", "account_name"]
    ).iterrows():
        current_balance = format_currency(
            row["current_account_balance"],
            row["account_currency"],
            locale="en_US",
        )
        balance_delta = format_currency(
            -row["delta_transaction_amount"],
            row["account_currency"],
            locale="en_US",
        )
        color_toggle = "off" if -row["delta_transaction_amount"] == 0 else "normal"
        con.metric(
            label=f"{row['account_name']} :gray-background[:blue[{row['account_type_name']}]]",
            value=current_balance,
            delta=balance_delta,
            delta_color=color_toggle,
        )

# Category Spend viz
with block2[0]:
    st.subheader("Spending by Category", anchor=False)
    category_spend_args: filterArgs = {
        k: filter_args[k]
        for k in [
            "account_types_filter",
            "accounts_filter",
            "transaction_status_filter",
            "transfers_filter",
            "inflow_filter",
            "date_filter",
            "cumulative_calculation",
        ]
        if k in filter_args
    }
    category_spend_args["transfers_filter"] = False

    category_spend_df = filter_df(
        df_name="detailed_transactions_df", **category_spend_args
    )

    category_spend_fig = px.bar(
        category_spend_df, "transaction_category_name", "transaction_amount"
    )
    category_spend_fig.update_layout(
        hoverlabel=dict(bgcolor="#0E1117", font_size=16, font_family="Sans Serif")
    )
    st.plotly_chart(category_spend_fig, use_container_width=True)
