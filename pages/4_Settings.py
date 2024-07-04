import streamlit as st
from Dashboard import curr

base_currency = curr.get_base_currency()
st.selectbox(
    label="Base Currency",
    options=st.session_state["currencies_df"]["currency_abbr"],
    index=int(
        st.session_state["currencies_df"][
            st.session_state["currencies_df"]["currency_abbr"] == base_currency
        ].index[0]
    ),
)