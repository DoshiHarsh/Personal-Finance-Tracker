# Budget

## Introduction to the Budget Dashboard

The budget dashboard is meant to be a privacy focused app to track your financial health to build towards your financial goals. 
It is meant to be a self hosted (either locally or on a cloud hosting service of your preference) service so that you can control who has access to your private financial data. Built using Streamlit, you can easily customize it to your needs. Currently is built on a sqlite3 database but there is planned work to enable you do any database you'd like (via SQLAlchemy).
If you'd like to contribute, please feel free to fork the repo or submit merge requests, ideas or issues.


## Prerequisites to run

- Local python installation
- pip install -r requirements.txt
- Streamlit run Dashboard.py


## Current features

- Create transaction categories and accounts in multiple currencies.
- Track points and rewards on your cards.
- And add transactions to add your expenses and income.
- Transfer money between accounts with currency rate conversion and origin/destination transfer fees.
- Visualize spending and current account balances. 


## To-do

For a detailed overview of planned work and priorities visit the [Project Board](https://github.com/users/DoshiHarsh/projects/2/views/2)

- User Authentication
    - Email login
    - Password Reset
    - Secure database connection and files

- Card UI
    - Card UI for viewing transaction/accounts/categories
    - Edit/delete values transaction/accounts/categories

- Account reconciliation
    - See last reconciled amounts and dates.
    - View and edit transactions since last reconciliation.
    - Override and update original starting balance by adding current accurate value.

- Investment tracking
    - Investment account creations/fields
    - Investment transaction tracking (ETF, Individual stocks, Mutual funds, Options)
    - RSU/Stock options transactions
    - Update current value of investment assets (as of date)
    - Net worth progress 

- Spending and Saving goals
    - Automatic allocations towards goals from income (Monthly/ Yearly/ Per paycheck)
    - Transactions tagged towards spending goals
   
- Currency support enhancements
    - Convert all currencies to base currency
    - Ability to update base currency 
    - Spend path currency conversions (default to base currency) At transaction time or current?
    - Api based accurate conversions to base currency 
    - Add currency details, symbols, flags

- Database enhancements
    - Update SQL config for modularity (SQLAlchemy based)
    - Streamline SQL transformations for data entry and visualization
    - Download the .db/.csv file

- UI and UX enhancements
    - Transaction filters order based on use frequency
    - Add logos to all categories
    - Add logo set for customization by users
    - Model previous monthly spend paths as display them as an underlay
    - Add animations throughout the UI 
    - Improve Error Handling and Logging
    - Streamlit cloud deployment via GitHub
    - Google Drive/OneDrive backup support

- Visualization enhancements
    - Dashboard items clickable onto relevant page (query support)
    - Sankey Diagram for income and spending
    - Graph for progress towards goal targets
    - Graph for account value change over time 
    - Debt rundown chart
    - Total net worth metric

- Transaction enhancements
    - Automatic Recurring Transactions
    - Timezone considerations for date fields in transactions
    - Split transactions between accounts
    - Add transaction and refund amount (split it between friends)
    - Easy transactions refunds

- Transfer enhancements
    - Loan Payment transactions
    - Credit card bill payment transactions

-  Account enhancements
    - RSU/Stock options income related fields for UI
    - Joint accounts with other users on instance

- Rewards enhancements
    - Ability to add rewards as statement credit during transactions
    - Ability to use reward points as payment method for transactions
    - Ability to transfer rewards points to bank/ credit card accounts

- Ambitious
    - OCR/AI model to read and add transactions from statements
    - LLM spending review and suggestions towards managing finances better
    - Connect with services like plaid to auto-import data


## Attributions

Currency rates implemented using Free API from [Exchange Rate API[(https://www.exchangerate-api.com)


## License




## Resources and Links

Currency:-
    - More robust currency support https://babel.pocoo.org/en/latest/api/numbers.html
    - Reorder currency based on most used

Database:-
    - SQLAlchemy ORM https://auth0.com/blog/sqlalchemy-orm-tutorial-for-python-developers/
    - Passwords https://devguide.dev/blog/store-encrypted-passwords-sqlite-python-sqlalchemy-bcrypt
    - JSON based full audit log https://til.simonwillison.net/sqlite/json-audit-log

- Streamlit
    Hover on tabs https://github.com/Socvest/streamlit-on-Hover-tabs
    Lottie animations https://extras.streamlit.app/
    User logins https://github.com/GauriSP10/streamlit_login_auth_ui
    Customizable widget like layout for dashboard https://github.com/okld/streamlit-elements
    Option Menu https://github.com/victoryhb/streamlit-option-menu
    Extras https://arnaudmiribel.github.io/streamlit-extras/extras/annotated_text/
    https://github.com/nicedouble/StreamlitAntdComponents
    https://github.com/gagan3012/streamlit-tags
    https://st-experimental-fragment.streamlit.app/Two_charts
    https://plotly.com/python/sankey-diagram/
    -https://stackoverflow.com/questions/55301343/how-to-define-the-structure-of-a-sankey-diagram-using-a-pandas-dataframe




