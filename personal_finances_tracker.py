import streamlit as st

st.set_page_config(layout="wide")

dashboard_page = st.Page(
    "pages/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True
)
categories_page = st.Page(
    "pages/categories.py", title="Categories", icon=":material/category:"
)
accounts_page = st.Page(
    "pages/accounts.py", title="Accounts", icon=":material/account_balance_wallet:"
)
transactions_page = st.Page(
    "pages/transactions.py", title="Transactions", icon=":material/receipt_long:"
)
settings_page = st.Page(
    "pages/settings.py", title="Settings", icon=":material/settings:"
)
accounts_reconciliation_page = st.Page(
    "pages/account_reconciliation.py",
    title="Reconcile Account",
    icon=":material/calculate:",
)

st.sidebar.page_link(
    "pages/dashboard.py", label="Dashboard", icon=":material/dashboard:"
)
st.sidebar.page_link(
    "pages/categories.py", label="Categories", icon=":material/category:"
)
st.sidebar.page_link(
    "pages/accounts.py", label="Accounts", icon=":material/account_balance_wallet:"
)
st.sidebar.page_link(
    "pages/transactions.py", label="Transactions", icon=":material/receipt_long:"
)
st.sidebar.page_link("pages/settings.py", label="Settings", icon=":material/settings:")

pg = st.navigation(
    [
        dashboard_page,
        categories_page,
        accounts_page,
        transactions_page,
        settings_page,
        accounts_reconciliation_page,
    ],
    position="hidden",
)
pg.run()
