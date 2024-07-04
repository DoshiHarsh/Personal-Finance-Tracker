import streamlit as st
import pandas as pd
import numpy as np
from Dashboard import db_operations, get_database_tables


@st.experimental_dialog("Add new Transaction", width="large")
@st.experimental_fragment()
def new_transaction_dialog():
    block1 = st.columns([3, 3, 2])
    merchant = block1[0].selectbox(
        "Merchant/Location",
        options=np.append(
            st.session_state["cashflow_transactions_df"][
                "transaction_merchant_name"
            ].unique(),
            ["<New value>"],
        ),
    )
    if merchant == "<New value>":
        new_merchant = block1[0].text_input("Add new Merchant/Location")
        final_merchant = new_merchant
    else:
        final_merchant = merchant
    account_name = block1[1].selectbox(
        "Account", options=st.session_state["accounts_df"]["account_name"]
    )
    account_details = st.session_state["accounts_df"][
        st.session_state["accounts_df"]["account_name"] == account_name
    ].reset_index(drop=True)
    transaction_date = block1[2].date_input(label="Transaction Date", value="today")

    block2 = st.columns(2)
    category = block2[0].selectbox(
        "Category",
        options=st.session_state["categories_df"]["category_name"].sort_values(),
    )
    category_details = st.session_state["categories_df"][
        st.session_state["categories_df"]["category_name"] == category
    ].reset_index(drop=True)
    sub_category = block2[1].selectbox(
        "Sub Category",
        options=np.append(
            st.session_state["cashflow_transactions_df"][
                "transaction_sub_category"
            ].unique(),
            ["<New value>"],
        ),
    )
    if sub_category == "<New value>":
        new_sub_category = block2[1].text_input("Add new Sub Category")
        final_sub_category = new_sub_category
    else:
        final_sub_category = sub_category

    block3 = st.columns(2)
    transaction_currency = block3[0].selectbox(
        "Currency", options=account_details["account_currency"], index=0, disabled=True
    )
    transaction_amount = block3[0].number_input("Amount", value=0.00)
    rewards_enabled = account_details["account_rewards"][0]
    if rewards_enabled:
        rewards_account_id = st.session_state["rewards_accounts_df"][
            st.session_state["rewards_accounts_df"]["linked_account_id"]
            == account_details["account_id"][0]
        ].reset_index(drop=True)["rewards_account_id"][0]
    else:
        rewards_account_id = None
    rewards_percentage = block3[1].number_input(
        "Rewards Percentage (%)", value=0.00, step=0.5, disabled=not rewards_enabled
    )
    rewards_calculation = round(transaction_amount * (rewards_percentage / 100), 2)
    rewards_amount = block3[1].number_input(
        "Rewards Amount", value=rewards_calculation, disabled=not rewards_enabled
    )
    transaction_total = float(transaction_amount - rewards_amount)

    transaction_notes = st.text_area(label="Transaction Notes")
    submit_enabled = (
        final_merchant
        and account_name
        and transaction_currency
        and category
        and transaction_amount
    )
    if st.button("Add Transaction", disabled=not submit_enabled):
        new_transaction = pd.DataFrame(
            {
                "transaction_merchant_name": [final_merchant],
                "transaction_account_id": [account_details["account_id"][0]],
                "transaction_date": [transaction_date],
                "transaction_category_id": [category_details["category_id"][0]],
                "transaction_sub_category": [final_sub_category],
                "transaction_currency": [transaction_currency],
                "transaction_amount": [transaction_amount],
                "rewards_account_id": [(rewards_account_id)],
                "rewards_percentage": [
                    round((rewards_amount / transaction_amount) * 100, 2)
                ],
                "rewards_amount": [rewards_amount],
                "transaction_total": [transaction_total],
                "transaction_notes": [transaction_notes],
                "transaction_status": ["Pending"],
            }
        )
        db_operations.table_insert(
            table_name="cashflow_transactions", df=new_transaction
        )
        del (
            st.session_state["cashflow_transactions_df"],
            st.session_state["detailed_transactions_df"],
        )
        get_database_tables(["cashflow_transactions", "detailed_transactions"])
        st.rerun()


st.title("Transactions")

block1 = st.columns([7, 2])
if block1[1].button("Add new Transaction", use_container_width=True):
    new_transaction_dialog()

st.dataframe(st.session_state["detailed_transactions_df"], hide_index=True)
