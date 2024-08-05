import streamlit as st
import pandas as pd
from babel.numbers import format_currency
from core_components.functions import (
    display_filter_ui,
    display_card_ui,
    filter_df,
    db_operations,
    today,
    account_dialog,
    get_current_account_balances,
)


for table in [
    "detailed_accounts",
    "detailed_transactions",
    "detailed_transfers",
    "detailed_rewards_accounts",
]:
    if f"{table}_df" not in st.session_state:
        st.session_state[f"{table}_df"] = db_operations.table_query(
            f"Select * from {table}"
        )

st.session_state["detailed_transfers_df"]["transfer_date"] = pd.to_datetime(
    st.session_state["detailed_transfers_df"]["transfer_date"]
)
st.session_state["detailed_transactions_df"]["transaction_date"] = pd.to_datetime(
    st.session_state["detailed_transactions_df"]["transaction_date"]
)
st.session_state["current_account_balances_df"]["account_last_reconciled"] = (
    pd.to_datetime(
        st.session_state["current_account_balances_df"]["account_last_reconciled"]
    )
)
st.session_state["current_account_balances_df"] = get_current_account_balances(
    st.session_state["detailed_transactions_df"],
    st.session_state["detailed_accounts_df"],
)

block1 = st.columns([6, 2], vertical_alignment="bottom")
block1[0].title("Reconcile Account", anchor=False)
if block1[1].button("Back to Accounts Page", use_container_width=True):
    del st.session_state["reconciliation_account"]
    st.switch_page("pages/accounts.py")

st.divider()

if "reconciliation_account" in st.session_state:
    account_details = (
        st.session_state["current_account_balances_df"]
        .loc[
            st.session_state["current_account_balances_df"]["account_name"]
            == st.session_state["reconciliation_account"]["account_name"]
        ]
        .iloc[0]
    )
    block2 = st.columns([5, 3, 2], vertical_alignment="bottom")
    block2[0].header(account_details["account_name"], anchor=False)

    with block2[1].popover(
        "Mark as reconciled",
    ):
        if st.button("Mark as reconciled", type="primary"):
            reconciliation_df = pd.DataFrame(
                {"account_last_reconciled": [today.date()]}
            )
            db_operations.table_update(
                table_name="accounts",
                id_col="account_id",
                val=account_details["account_id"],
                df=reconciliation_df,
            )
            del (
                st.session_state["reconciliation_account"],
                st.session_state["detailed_accounts_df"],
            )
            st.switch_page("pages/accounts.py")
    block2[2].button(
        "Edit Account",
        on_click=account_dialog,
        args=[account_details.to_dict()],
        use_container_width=True,
    )

    block3 = st.columns([2, 2, 2, 2], vertical_alignment="bottom")
    block3[0].metric(
        label="Settled Balance",
        value=format_currency(
            account_details["current_account_balance"],
            account_details["account_currency"],
            locale="en_US",
        ),
    )
    block3[2].metric(
        label="Total Balance",
        value=format_currency(
            account_details["pending_account_balance"],
            account_details["account_currency"],
            locale="en_US",
        ),
    )

    filter_args = display_filter_ui(
        type="account_reconciliation_filters",
        last_reconciliation=account_details["account_last_reconciled"],
    )
    filter_args["accounts_filter"] = [account_details["account_name"]]

    account_transactions = filter_df(
        df_name="detailed_transactions_df", **filter_args
    ).sort_values("transaction_date", ascending=False)

    display_card_ui(account_transactions, type="transactions")
