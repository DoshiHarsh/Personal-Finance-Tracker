# Personal Finance Tracker

## Introduction to the Personal Finance Tracker

The Personal Finance Tracker is meant to be a privacy focused tool to help track your financial health to build towards your goals. 
You can host it either locally or on a cloud hosting service of your preference, giving you control on who has access to your private financial data. Built using Streamlit, you can easily customize it to your needs. The backend is currently built on a sqlite3 database but there is planned work to enable you do any database you'd like (via SQLAlchemy).

If you'd like to contribute, please feel free to fork the repo, submit pull requests, ideas, or issues.

## Prerequisites to run

To add dummy data while initialization for the first run, please replace the values in [db_config.json](/files/db_config.json) with the values in [dev_db_config.json](/files/dev_db_config.json) before running the streamlit run command.

- local Python (>3.11) installation. Using python version management like pyenv, or virtualenv is recommended. 
- pip install -r requirements.txt
- streamlit run Dashboard.py
 

## Current features

- Create, edit, and delete categories and accounts.
- Track reward points, miles and dollars (or local equivalent) on your reward accounts.
- Add transactions for your expenses and income.
- Transfer money between accounts with currency rate conversions and origin/destination transfer fees.
- Visualize spending, current account balances and spend by category over time.


## Walkthrough (To-do)

- Create accounts.
- Create transactions and transfers.
- See graphs to track them on the dashboard page.


## Planned Work

For a up to date overview of completed, planned work and priorities visit the [Project Board](https://github.com/users/DoshiHarsh/projects/2/views/2).

- Account reconciliation
    - See last reconciled amounts and dates.
    - View and edit transactions since last reconciliation
    - Override and update original starting balance by adding current accurate value.

- Spending and Saving goals
    - Automatic allocations towards goals from income (Monthly/ Yearly/ Per paycheck)
    - Transactions tagged towards spending goals

- User Authentication
    - Email login
    - Password Reset
    - Secure database connection and files

- Investment tracking
    - Investment account creations/fields
    - Investment transaction tracking (ETF, Individual stocks, Mutual funds, Options)
    - RSU/Stock options transactions
    - Update current value of investment assets (as of date)
    - Net worth progress 
   
- Currency support enhancements
    - Convert all currencies to base currency
    - Ability to update base currency 
    - Spend path currency conversions (default to base currency) At transaction time or current?
    - Api based accurate conversions to base currency 
    - Add currency details, symbols, flags

- Database enhancements
    - Update SQL config for modularity (SQLAlchemy based)
    - Support for additional databases for flexibility (Postgres, duckDB?)
    - Streamline SQL transformations for data entry and visualization
    - Download the .db/.csv file

- UI and UX enhancements
    - Transaction filters order based on use frequency
    - Add general help tooltips throughout the UI
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

- Automation Goals (Long-Term)
    - OCR/AI model to read and add transactions from statements
    - LLM spending review and suggestions towards managing finances better
    - Connect with services like plaid to auto-import data


## Attributions

Currency rates implemented using Free API from [Exchange Rate API](https://www.exchangerate-api.com).


## License

[AGPL-V3.0 License](/LICENSE)


## Resources and Links

- Currency:-
    - More robust currency support https://babel.pocoo.org/en/latest/api/numbers.html
    - Reorder currency based on most used

- Database:-
    - SQLAlchemy ORM https://auth0.com/blog/sqlalchemy-orm-tutorial-for-python-developers/
    - Passwords https://devguide.dev/blog/store-encrypted-passwords-sqlite-python-sqlalchemy-bcrypt
    - JSON based full audit log https://til.simonwillison.net/sqlite/json-audit-log

- Streamlit
    - Hover on tabs https://github.com/Socvest/streamlit-on-Hover-tabs
    - Lottie animations https://extras.streamlit.app/
    - User logins https://github.com/GauriSP10/streamlit_login_auth_ui
    - https://pypi.org/project/streamlit-authenticator/
    - Customizable widget like layout for dashboard https://github.com/okld/streamlit-elements
    - Option Menu https://github.com/victoryhb/streamlit-option-menu
    - Extras https://arnaudmiribel.github.io/streamlit-extras/extras/annotated_text/
    - https://github.com/nicedouble/StreamlitAntdComponents
    - https://github.com/gagan3012/streamlit-tags
    - https://github.com/lukasmasuch/streamlit-pydantic?tab=readme-ov-file#examples
    - https://st-experimental-fragment.streamlit.app/Two_charts
    - https://plotly.com/python/sankey-diagram/
    - https://stackoverflow.com/questions/55301343/how-to-define-the-structure-of-a-sankey-diagram-using-a-pandas-dataframe
    - https://medium.com/streamlit/paginating-dataframes-with-streamlit-2da29b080920

- Services:
    - https://heliohost.org/tommy/#donate
    - https://aiven.io/docs/platform/concepts/free-plan#free-plan-features-and-limitations

- Miscellaneous:
    - https://towardsdatascience.com/part-1-a-guide-for-optimizing-your-data-science-workflow-53add6481556