import streamlit as st

dashboard_page = st.Page("pages/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True)
categories_page = st.Page("pages/categories.py", title="Categories", icon=":material/category:")
accounts_page = st.Page("pages/accounts.py", title="Accounts", icon=":material/account_balance_wallet:")
transactions_page = st.Page("pages/transactions.py", title="Transactions", icon=":material/receipt_long:")
settings_page = st.Page("pages/settings.py", title="Settings", icon=":material/settings:")
#accounts_reconciliation_page = st.Page("")

pg = st.navigation([dashboard_page, categories_page, accounts_page, transactions_page, settings_page])
pg.run()