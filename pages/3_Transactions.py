import streamlit as st
from core_components.functions import db_operations
import pandas as pd
from core_components.functions import (
    display_card_ui,
    display_filter_ui,
    transaction_dialog,
    filter_df,
    get_current_account_balances,
)


# Due to unknown limitation, setting values to st.session_state with function defined in another script doesn't always execute.
for table in [
    "categories",
    "detailed_accounts",
    "detailed_transactions",
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

st.session_state["detailed_transactions_df"]["transaction_date"] = pd.to_datetime(
    st.session_state["detailed_transactions_df"]["transaction_date"]
)

block0 = st.columns([6, 2], vertical_alignment="bottom")
block0[0].title("Transactions")
block0[1].button(
    "New Transaction", on_click=transaction_dialog, use_container_width=True
)
card_ui_args = display_filter_ui(type="transaction_filters")
transactions_df = filter_df(
    df_name="detailed_transactions_df", **card_ui_args
).sort_values("transaction_date", ascending=False)
display_card_ui(display_df=transactions_df, type="transactions")
