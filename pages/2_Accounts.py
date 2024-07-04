import streamlit as st
import pandas as pd
from Dashboard import db_operations, curr, get_database_tables


@st.experimental_dialog("Add new Account")
@st.experimental_fragment()
def new_account_dialog():
    with st.container():
        account_name = st.text_input(placeholder="ex. BoFA", label="Account Name")

        block1 = st.columns([8, 1], vertical_alignment="bottom")
        account_type = block1[0].selectbox(
            options=st.session_state["account_types_df"]["account_type_name"],
            label="Type",
            index=None,
        )
        account_type_details = st.session_state["account_types_df"][
            st.session_state["account_types_df"]["account_type_name"] == account_type
        ].reset_index(drop=True)
        with block1[1].popover(r"\+"):
            new_account_type = st.text_input(
                placeholder="Add new account type", label="Add new account type"
            )
            if st.button(label="Add"):
                db_operations.table_insert(
                    table_name="account_types",
                    df=pd.DataFrame({"account_type_name": [new_account_type]}),
                )
                del st.session_state["account_types_df"]
                get_database_tables(["account_types"])
                st.rerun()

        block2 = st.columns([4, 5])
        account_currency = block2[0].selectbox(
            options=st.session_state["currencies_df"]["currency_abbr"],
            label="Select Account Currency",
            index=None,
        )
        account_starting_balance = block2[1].number_input(
            label="Account Balance", value=0.0
        )

        account_rewards = st.toggle(
            label="Rewards Account?",
            help="You can add reward categories after the account is added.",
        )
        if account_rewards:
            rewards_account_type = st.selectbox(
                options=["Points", "Miles", f"{account_currency} value"],
                label="Rewards Account Type",
                index=None,
            )
            if rewards_account_type == "Points" or rewards_account_type == "Miles":
                point_value = st.number_input(
                    placeholder=f"{account_currency} per {rewards_account_type.rstrip('s')}",
                    label=f"{rewards_account_type} Value",
                    value=None,
                )
            else:
                point_value = 1.0
            starting_rewards_balance = st.number_input(
                label="Starting Rewards Balance", value=0.0
            )

        submit_enabled = account_name and account_type and account_currency
        if st.button("Submit", key="add_account", disabled=not submit_enabled):
            new_account = pd.DataFrame(
                {
                    "account_name": [account_name],
                    "account_type_id": [account_type_details["account_type_id"][0]],
                    "account_starting_balance": [account_starting_balance],
                    "account_currency": [account_currency],
                    "account_rewards": [account_rewards],
                }
            )
            db_operations.table_insert(table_name="accounts", df=new_account)
            linked_account_id = db_operations.table_query(
                f"Select account_id from accounts where account_name='{account_name}'"
            )["account_id"][0]

            if account_rewards:
                new_rewards_account = pd.DataFrame(
                    {
                        "linked_account_id": [linked_account_id],
                        "rewards_type": [rewards_account_type],
                        "rewards_point_value": [point_value],
                        "starting_rewards_balance": [starting_rewards_balance],
                    }
                )
                db_operations.table_insert(
                    table_name="rewards_accounts", df=new_rewards_account
                )
            del (
                st.session_state["accounts_df"],
                st.session_state["rewards_accounts_df"],
                st.session_state["detailed_accounts_df"],
                st.session_state["detailed_rewards_accounts_df"],
            )
            get_database_tables(
                [
                    "accounts",
                    "rewards_accounts",
                    "detailed_accounts",
                    "detailed_rewards_accounts",
                ]
            )
            st.rerun()


@st.experimental_dialog("Record a Transfer", width="large")
@st.experimental_fragment()
def new_transfer_dialog():
    with st.container():
        origin_account = st.selectbox(
            options=st.session_state["accounts_df"]["account_name"],
            label="Origin Account",
            index=None,
        )
        origin_account_details = st.session_state["accounts_df"][
            st.session_state["accounts_df"]["account_name"] == origin_account
        ].reset_index(drop=True)

        destination_account = st.selectbox(
            options=st.session_state["accounts_df"][
                st.session_state["accounts_df"]["account_name"] != origin_account
            ]["account_name"],
            label="Destination Account",
            index=None,
        )
        destination_account_details = st.session_state["accounts_df"][
            st.session_state["accounts_df"]["account_name"] == destination_account
        ].reset_index(drop=True)

        transfer_date = st.date_input(label="Transfer Date", value="today")

        block1 = st.columns([4, 4])
        origin_transfer_charges = block1[0].number_input(
            label="Origin Transfer Charges", value=0.00
        )
        destination_transfer_charges = block1[1].number_input(
            label="Destination Transfer Charges", value=0.00
        )

        conversion_rate = 1.0
        if isinstance(origin_account, str) & isinstance(destination_account, str):
            if (
                origin_account_details["account_currency"][0]
                != destination_account_details["account_currency"][0]
            ):
                block2 = st.columns([4, 4, 4])
                origin_currency = block2[0].selectbox(
                    options=origin_account_details["account_currency"],
                    index=0,
                    label="Origin Currency",
                    disabled=True,
                )
                destination_currency = block2[1].selectbox(
                    options=destination_account_details["account_currency"],
                    index=0,
                    label="Destination Currency",
                    disabled=True,
                )
                conversion_rate_value = curr.get_currency_conversion_rate(
                    origin_currency,
                    destination_currency,
                    st.session_state["currency_rates_df"],
                )
                conversion_rate = block2[2].number_input(
                    label="Conversion Rate", value=conversion_rate_value, format="%.6f"
                )
            else:
                origin_currency = destination_currency = origin_account_details[
                    "account_currency"
                ][0]

        send_amount = st.number_input(label="Sent Amount", value=0.00)
        received_amount_calc = (
            send_amount * conversion_rate
        ) - destination_transfer_charges
        received_amount = st.number_input(
            label="Received Amount", value=received_amount_calc
        )
        transfer_notes = st.text_area(label="Transfer Notes")

        submit_enabled = (
            origin_account and destination_account and transfer_date and send_amount
        )
        if st.button("Submit", key="new_transfer", disabled=not submit_enabled):
            new_transfer = pd.DataFrame(
                {
                    "transfer_date": [transfer_date],
                    "origin_account_id": [origin_account_details["account_id"][0]],
                    "destination_account_id": [
                        destination_account_details["account_id"][0]
                    ],
                    "origin_send_amount": [send_amount],
                    "origin_currency": [origin_currency],
                    "origin_transfer_charges": [origin_transfer_charges],
                    "currency_conversion_rate": [
                        (received_amount + destination_transfer_charges) / send_amount
                    ],
                    "destination_received_amount": [received_amount],
                    "destination_currency": [destination_currency],
                    "destination_transfer_charges": [destination_transfer_charges],
                    "is_destination_rewards_account": [False],
                    "transfer_notes": [transfer_notes],
                }
            )

            category_id = st.session_state["categories_df"][
                st.session_state["categories_df"]["category_name"] == "Account Transfer"
            ].reset_index()["category_id"][0]
            new_transaction = pd.DataFrame(
                {
                    "transaction_merchant_name": [
                        f"{origin_account} -> {destination_account} Transfer",
                        f"{origin_account} -> {destination_account} Transfer",
                    ],
                    "transaction_account_id": [
                        origin_account_details["account_id"][0],
                        destination_account_details["account_id"][0],
                    ],
                    "transaction_date": [transfer_date, transfer_date],
                    "transaction_category_id": [category_id, category_id],
                    "transaction_sub_category": [None, None],
                    "transaction_currency": [origin_currency, destination_currency],
                    "transaction_amount": [
                        send_amount + origin_transfer_charges,
                        -(received_amount - destination_transfer_charges),
                    ],
                    "rewards_account_id": [None, None],
                    "rewards_percentage": [0.00, 0.00],
                    "rewards_amount": [0.00, 0.00],
                    "transaction_total": [
                        send_amount + origin_transfer_charges,
                        -(received_amount - destination_transfer_charges),
                    ],
                    "transaction_notes": [transfer_notes, transfer_notes],
                    "transaction_status": ["Complete", "Complete"],
                }
            )
            db_operations.table_insert(table_name="cashflow_transfers", df=new_transfer)
            db_operations.table_insert(
                table_name="cashflow_transactions", df=new_transaction
            )
            del (
                st.session_state["cashflow_transfers_df"],
                st.session_state["cashflow_transactions_df"],
                st.session_state["detailed_transactions_df"],
                st.session_state["detailed_transfers_df"],
            )
            get_database_tables(
                [
                    "cashflow_transfers",
                    "cashflow_transactions",
                    "detailed_transfers",
                    "detailed_transactions",
                ]
            )
            st.rerun()


st.title("Accounts")

block1 = st.columns([5, 2, 2])
if block1[1].button("Add new Account", use_container_width=True):
    new_account_dialog()
if block1[2].button("Record a transfer", use_container_width=True):
    new_transfer_dialog()

st.dataframe(st.session_state["detailed_accounts_df"], hide_index=True)
st.dataframe(st.session_state["detailed_transactions_df"], hide_index=True)
st.dataframe(st.session_state["detailed_transfers_df"], hide_index=True)
