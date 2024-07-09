import streamlit as st
from Dashboard import db_operations
from core_components.functions import populate_list
from collections import defaultdict
import pandas as pd
import numpy as np

# Due to unknown limitation, setting values to st.session_state with function defined in another script doesn't always execute.
for table in ["detailed_transactions"]:
    if f"{table}_df" not in st.session_state:
        st.session_state[f"{table}_df"] = db_operations.table_query(
            f"Select * from {table}"
        )

st.title("Testing")

# Display the transactions dataframe. (to be replaced with Card UI)
st.dataframe(st.session_state["detailed_transactions_df"], hide_index=True)

@st.experimental_dialog("Add new Transaction", width="large")
def edit_row(row=None):
    """
    Create dialog box UI to create new transaction.
    """

    if isinstance(row, tuple):
        None
    else:    
        row = defaultdict(lambda: None)
    
    with st.container():
        block1 = st.columns([3, 3, 2])
        merchant_options = populate_list(st.session_state["detailed_transactions_df"]["transaction_merchant_name"])
        merchant = block1[0].selectbox(
            "Merchant/Location",
            options=merchant_options,
            placeholder=(row.transaction_merchant_name or None),
            index=None
        )
        # New values cannot be typed in selectbox, thus creating new field.
        if merchant == "<New value>":
            new_merchant = block1[0].text_input("Add new Merchant/Location")
            final_merchant = new_merchant
        else:
            final_merchant = merchant
        account_name = block1[1].selectbox(
            "Account", options=st.session_state["detailed_accounts_df"]["account_name"]
        )
        account_details = st.session_state["detailed_accounts_df"][
            st.session_state["detailed_accounts_df"]["account_name"] == account_name
        ].reset_index(drop=True)
        transaction_date = block1[2].date_input(label="Transaction Date", value=(row.transaction_date or "today"))

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
            options=populate_list(
                st.session_state["detailed_transactions_df"]["transaction_sub_category"]
            ),
        )
        # New values cannot be typed in selectbox, thus creating new field.
        if sub_category == "<New value>":
            new_sub_category = block2[1].text_input("Add new Sub Category")
            final_sub_category = new_sub_category
        else:
            final_sub_category = sub_category

        block3 = st.columns(2)
        transaction_currency = block3[0].selectbox(
            "Currency",
            options=account_details["account_currency"],
            index=0,
            disabled=True,
        )
        transaction_amount = block3[0].number_input("Amount", value=0.00)
        rewards_enabled = account_details["account_rewards"][0]
        if rewards_enabled:
            rewards_account_id = st.session_state["detailed_accounts_df"][
                st.session_state["detailed_accounts_df"]["linked_account_id"]
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
            del st.session_state["detailed_transactions_df"]
            st.rerun()

if st.button("haha"):
    edit_row()
st.session_state["detailed_transactions_df"]["transaction_date"] = pd.to_datetime(st.session_state["detailed_transactions_df"]["transaction_date"])

block = st.columns(2)
left_con = block[0].container()
right_con = block[1].container()

for row in st.session_state["detailed_transactions_df"].reset_index(drop=True).itertuples():

    con = None    
    if getattr(row, 'Index') % 2 == 0:
        con = left_con.container(border=True)
    else:
        con = right_con.container(border=True)
        
    row0 = con.columns([10,1],vertical_alignment="center")
    row0[1].button("✎", key=f"del_{row.transaction_merchant_name}_{row.transaction_id}", on_click=edit_row, args=[row],use_container_width=True)
    row0[0].write(f"{row.transaction_merchant_name}_{row.transaction_id}")
    id = con.text_input(label="transaction_merchant_name", value = row.transaction_merchant_name,
                        key=f"{row.transaction_merchant_name}_{row.transaction_id}", disabled=True)
    



"""
To-do

1. Build alter table database function.
2. Update dialog functions to set default values, change button to Update transaction to call alter table.
3. Mark transactions as complete.
4. Delete a transaction.
4. Build filters, etc to UI to search and filter through transactions, transfers, accounts, etc.
5. Pagination.
6. Tabs for Multiple Card UI's in a single page.
7. Card UI elements with important fields. (Without a lot of hardcoding)



"""