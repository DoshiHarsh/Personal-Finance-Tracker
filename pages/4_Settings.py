import streamlit as st
from Dashboard import curr

base_currency = curr.get_base_currency()
# To-do, add callback to change base currency and get new rates when changed.
st.selectbox(
    label="Base Currency",
    options=st.session_state["currencies_df"]["currency_abbr"],
    index=int(
        st.session_state["currencies_df"][
            st.session_state["currencies_df"]["currency_abbr"] == base_currency
        ].index[0]
    ),
    disabled=True
)
