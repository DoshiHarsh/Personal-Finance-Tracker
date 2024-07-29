import streamlit as st
from core_components.functions import db_operations, curr

base_currency = curr.get_base_currency()

for table in ["currencies"]:
    if f"{table}_df" not in st.session_state:
        st.session_state[f"{table}_df"] = db_operations.table_query(
            f"Select * from {table}"
        )

# To-do, add callback to change base currency and get new rates when changed.
st.selectbox(
    label="Base Currency",
    options=st.session_state["currencies_df"]["currency_abbr"],
    index=int(
        st.session_state["currencies_df"][
            st.session_state["currencies_df"]["currency_abbr"] == base_currency
        ].index[0]
    ),
    disabled=True,
)
