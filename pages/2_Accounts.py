import streamlit as st
import pandas as pd
from core_components.functions import (
    db_operations,
    display_card_ui,
    account_dialog,
    transfer_dialog,
    display_filter_ui,
    filter_df,
    get_current_account_balances,
)


# Due to unknown limitation, setting values to st.session_state with function defined in another script doesn't always execute.
for table in [
    "detailed_accounts",
    "detailed_transfers",
    "detailed_rewards_accounts",
    "currencies",
    "account_types",
]:
    if f"{table}_df" not in st.session_state:
        st.session_state[f"{table}_df"] = db_operations.table_query(
            f"Select * from {table}"
        )
st.session_state["current_account_balances_df"] = get_current_account_balances(
    st.session_state["detailed_transactions_df"],
    st.session_state["detailed_accounts_df"],
)
st.session_state["detailed_transfers_df"]["transfer_date"] = pd.to_datetime(
    st.session_state["detailed_transfers_df"]["transfer_date"]
)

block1 = st.columns([5, 2, 2], vertical_alignment="bottom")
block1[0].title("Accounts")
block1[1].button("New Account", on_click=account_dialog, use_container_width=True)
block1[2].button("New Transfer", on_click=transfer_dialog, use_container_width=True)

tabs = st.tabs(["Accounts", "Transfers"])
with tabs[0]:
    account_filter_args = display_filter_ui(type="account_filters")
    accounts_df = filter_df(
        df_name="current_account_balances_df", **account_filter_args
    ).sort_values("account_name")
    display_card_ui(display_df=accounts_df, type="accounts")

with tabs[1]:
    transfer_filter_args = display_filter_ui(type="transfer_filters")
    transfers_df = filter_df(
        df_name="detailed_transfers_df", **transfer_filter_args
    ).sort_values("transfer_date", ascending=False)
    display_card_ui(display_df=transfers_df, type="transfers")
