import requests
import numpy as np
import pandas as pd
import json
from typing import List, Optional
from core_components.database import ConnectDB
import streamlit as st
import math
from babel.numbers import format_currency
from datetime import datetime, timedelta
from typing import Unpack, TypedDict, Tuple

today = datetime.today()
db_operations = ConnectDB("budget_db")


class filterArgs(TypedDict, total=False):
    account_types_filter: List
    account_currency_filter: List
    account_rewards_filter: List
    is_active_filter: bool
    accounts_filter: List
    date_filter: Tuple[datetime, datetime]
    categories_types_filter: List
    transaction_status_filter: List
    transfers_filter: bool
    inflow_filter: bool
    cumulative_calculation: bool
    origin_account_filter: List
    destination_account_filter: List


class Currencies:
    def __init__(self, db_operations: ConnectDB) -> None:
        """
        Initializes class with database connection and api endpoint.

        Parameters
        ----------
        db_operations: ConnectDB
            Initialized class variable of type ConnectDB.

        Returns
        ----------
        `None`
        """
        self.api_endpoint = "https://open.er-api.com/v6/latest/USD"
        self.db_operations = db_operations

    def get_base_currency(self, table_name: str = "currencies") -> Optional[str]:
        """
        Get base currency abbreviation from the database table containing a boolean `is_base_currency` field.

        Parameters
        ----------
        table_name: str, default="currencies"
            Name of table in the database to get base currency abbreviation from.

        Returns
        -------
        `str` with base currency name. `None` if any errors.
        """
        try:
            base_currency = self.db_operations.table_query(
                f"Select currency_abbr from {table_name} where is_base_currency IS TRUE"
            )["currency_abbr"][0]
            return base_currency
        except Exception as e:
            print(e)
            return None

    def get_new_currency_rates(self) -> Optional[pd.DataFrame]:
        """
        Return new currency rates by querying `self.api_endpoint` and return result as pd.DataFrame.

        Returns
        -------
        `pd.DataFrame` with new currency rates. `None` if any errors.
        """
        new_rates = json.loads(requests.get(self.api_endpoint).text)
        if new_rates["result"] == "success":
            df = (
                pd.DataFrame.from_dict(new_rates["rates"], orient="index")
                .reset_index()
                .rename(columns={"index": "currency_abbr", 0: "currency_rate"})
            )
            df[["base_currency", "currency_update_timestamp"]] = [
                (self.get_base_currency() or "USD"),
                new_rates["time_last_update_unix"],
            ]
            return df
        else:
            # More verbose logging needed.
            print("Error response from API, aborting")
            return None

    def update_currency_rates(
        self, df: pd.DataFrame, table_name: str = "currency_rates"
    ) -> bool:
        """
        Update currency rates stored in the database.

        Parameters
        ----------
        df: pd.DataFrame
            DataFrame containing values to update the database table.

        table_name: str, default="currency_rates"
            Name of table in the database to update.

        Returns
        -------
        `True` if table successfully updated, `False` otherwise.
        """
        try:
            res1 = self.db_operations.raw_query(f"DELETE FROM {table_name}")
            res2 = self.db_operations.table_insert(
                table_name=table_name, df=df, if_exists="append"
            )
            return True if all((res1, res2)) else False
        except Exception as e:
            print(e)
            return False

    def update_currency_desc(
        self, currency_list: pd.Series, table_name: str = "currencies"
    ) -> bool:
        """
        Update currency description stored in the database. (currently uses placeholder empty values, to be updated)

        Parameters
        ----------
        df: pd.Series
            Series containing currency abbreviations to update the database table.

        table_name: str, default="currencies"
            Name of table in the database to update.

        Returns
        -------
        `True` if table successfully updated, `False` otherwise.
        """

        df = pd.DataFrame(currency_list)
        # To-do. Currently replaces with empty values, only retaining the base currency.
        df[["currency_symbol", "currency_description", "is_base_currency"]] = [
            "",
            "",
            False,
        ]
        df.loc[
            df["currency_abbr"] == (self.get_base_currency() or "USD"),
            "is_base_currency",
        ] = True
        try:
            self.db_operations.table_insert(
                table_name=table_name, df=df, if_exists="replace"
            )
            return True
        except Exception as e:
            print(e)
            return False

    def check_and_update_currency_rates(self) -> Optional[bool]:
        """
        Check API endpoint for new currency rates, and update database if newer rates available.

        Returns
        -------
        `True` if table successfully updated, `False` if error, `None` if table not updated.
        """
        try:
            current_timestamp_query = "Select max(currency_update_timestamp) as current_timestamp from currency_rates"
            current_timestamp = self.db_operations.table_query(current_timestamp_query)[
                "current_timestamp"
            ][0]
        except Exception as e:
            print(e)
            current_timestamp = 0

        new_rates_df = self.get_new_currency_rates()
        if new_rates_df["currency_update_timestamp"][0] > (current_timestamp or 0):
            res1 = self.update_currency_desc(new_rates_df["currency_abbr"])
            res2 = self.update_currency_rates(new_rates_df)
            return True if all((res1, res2)) else False
        else:
            return None

    def get_currency_conversion_rate(
        self,
        origin_currency: str,
        target_currency: str,
        currency_rates_df: Optional[pd.DataFrame] = None,
        table_name: Optional[str] = "currency_rates",
    ) -> Optional[float]:
        """
        Get currency conversion rates between origin and target currency.
        (Uses base currency as intermediary, to be updated for accuracy)

        Parameters
        ----------
        origin_currency: str
            Origin currency abbreviation.

        target_currency: str
            Target currency abbreviation.

        currency_rates_df: Optional[pd.DataFrame], default=None
            Optional DataFrame to use for currency rate calculations, queries the database otherwise.

        table_name: Optional[str], default="currency_rates"
            Name of table in the database to get currency rates from.

        Returns
        -------
        `float` with currency conversion rate. `None` if any errors.
        """
        try:
            if not isinstance(currency_rates_df, pd.DataFrame):
                currency_rates_df = self.db_operations.table_query(
                    f"Select * from {table_name}"
                )

            origin_to_base_rate = currency_rates_df.loc[
                currency_rates_df["currency_abbr"] == origin_currency, "currency_rate"
            ].iloc[0]
            target_to_base_rate = currency_rates_df.loc[
                currency_rates_df["currency_abbr"] == target_currency, "currency_rate"
            ].iloc[0]
            origin_to_target_rate = (1 / origin_to_base_rate) * target_to_base_rate

            return origin_to_target_rate
        except Exception as e:
            print(e)
            return None


def filter_df(df_name: str, **kwargs: Unpack[filterArgs]) -> pd.DataFrame:
    """
    Perform filter operations on DataFrame stored in st.session_state.

    Parameters
    ----------
    df_name: str, ["detailed_accounts_df", "current_account_balances_df", "detailed_transactions_df", "detailed_transfers_df"]
        DataFrame to perform filter operations on.

    **kwargs: Unpack[filterArgs]
        TypedDict with filters to apply on the DataFrame.

    Returns
    -------
    `pd.DataFrame` with filtered values.
    """
    df = st.session_state[df_name]
    # Defining the columns name for the specific DataFrame types.
    if df_name == "detailed_accounts_df" or df_name == "current_account_balances_df":
        cols = {
            "account_types_filter": "account_type_name",
            "account_currency_filter": "account_currency",
            "account_rewards_filter": "account_rewards",
            "is_active_filter": "is_active",
        }

        if "account_types_filter" in kwargs.keys():
            if len(kwargs["account_types_filter"]) > 0:
                df = df[
                    df[cols["account_types_filter"]].isin(
                        kwargs["account_types_filter"]
                    )
                ]
        if "account_currency_filter" in kwargs.keys():
            if len(kwargs["account_currency_filter"]) > 0:
                df = df[
                    df[cols["account_currency_filter"]].isin(
                        kwargs["account_currency_filter"]
                    )
                ]
        if "account_rewards_filter" in kwargs.keys():
            if len(kwargs["account_rewards_filter"]) > 0:
                df = df[
                    df[cols["account_rewards_filter"]].isin(
                        kwargs["account_rewards_filter"]
                    )
                ]
        if "is_active_filter" in kwargs.keys():
            if kwargs["is_active_filter"]:
                df = df[df[cols["is_active_filter"]] == True]
    elif df_name == "detailed_transactions_df":
        cols = {
            "account_types_filter": "transaction_account_type_name",
            "accounts_filter": "transaction_account_name",
            "categories_types_filter": "transaction_category_name",
            "date_filter": "transaction_date",
            "transaction_status_filter": "transaction_status",
            "transfers_filter": "transaction_merchant_name",
            "inflow_filter": "transaction_amount",
            "cumulative_calculation": "transaction_amount",
        }

        if "account_types_filter" in kwargs.keys():
            if len(kwargs["account_types_filter"]) > 0:
                df = df[
                    df[cols["account_types_filter"]].isin(
                        kwargs["account_types_filter"]
                    )
                ]
        if "accounts_filter" in kwargs.keys():
            if len(kwargs["accounts_filter"]) > 0:
                df = df[df[cols["accounts_filter"]].isin(kwargs["accounts_filter"])]
        if "date_filter" in kwargs.keys():
            df = df[
                pd.to_datetime(df[cols["date_filter"]]).between(
                    kwargs["date_filter"][0], kwargs["date_filter"][1]
                )
            ]
        if "categories_types_filter" in kwargs.keys():
            if len(kwargs["categories_types_filter"]) > 0:
                df = df[
                    df[cols["categories_types_filter"]].isin(
                        kwargs["categories_types_filter"]
                    )
                ]
        if "transaction_status_filter" in kwargs.keys():
            if len(kwargs["transaction_status_filter"]) > 0:
                df = df[
                    df[cols["transaction_status_filter"]].isin(
                        kwargs["transaction_status_filter"]
                    )
                ]
        if "transfers_filter" in kwargs.keys():
            if not kwargs["transfers_filter"]:
                df = df[
                    ~df[cols["transfers_filter"]].astype(str).str.contains("Transfer")
                ]
        if "inflow_filter" in kwargs.keys():
            if not kwargs["inflow_filter"]:
                df = df[((df[cols["inflow_filter"]] > 0))]
        # Always last step to ensure the zero value (for time series graph) is at index 0.
        if "cumulative_calculation" in kwargs.keys():
            if kwargs["cumulative_calculation"]:
                cumulative_calc = df.sort_values("transaction_date")[
                    "transaction_amount"
                ].cumsum()
                df = df.join(cumulative_calc, rsuffix="_cumulative").sort_values(
                    "transaction_date"
                )
                zero_val_df = pd.DataFrame(
                    {
                        "transaction_date": [df["transaction_date"].min()],
                        "transaction_amount_cumulative": [0],
                        "transaction_amount": [0],
                        "transaction_merchant_name": [""],
                    }
                )
                df = pd.concat([zero_val_df, df])
    elif df_name == "detailed_transfers_df":
        cols = {
            "origin_account_filter": "origin_account_name",
            "destination_account_filter": "destination_account_name",
            "date_filter": "transfer_date",
        }

        if "origin_account_filter" in kwargs.keys():
            if len(kwargs["origin_account_filter"]) > 0:
                df = df[
                    df[cols["origin_account_filter"]].isin(
                        kwargs["origin_account_filter"]
                    )
                ]
        if "destination_account_filter" in kwargs.keys():
            if len(kwargs["destination_account_filter"]) > 0:
                df = df[
                    df[cols["destination_account_filter"]].isin(
                        kwargs["destination_account_filter"]
                    )
                ]
        if "date_filter" in kwargs.keys():
            df = df[
                pd.to_datetime(df[cols["date_filter"]]).between(
                    kwargs["date_filter"][0], kwargs["date_filter"][1]
                )
            ]

    return df.reset_index(drop=True)


def df_summary(
    df: pd.DataFrame,
    groupby_cols: List | str,
    return_cols: List | str,
    rename_return_cols: Optional[List | str] = None,
    type: str = "sum",
) -> pd.DataFrame:
    """
    Perform groupby and summarize operations with optional renaming for output columns.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame to perform groupby and perform operation on.

    groupby_cols: List | str
        List of columns or str of single column name to perform groupby operation.

    return_cols: List | str
        List of columns or str of single column name to return.

    rename_return_cols: Optional[List | str], default=None
        List or str to rename output columns, must match length of `return_cols`.

    type: str, default="sum"
        Type of summarization operation to perform.

    Returns
    -------
    `pd.DataFrame` with summarized values.
    """
    if isinstance(rename_return_cols, str):
        rename_return_cols = [rename_return_cols]
    if isinstance(return_cols, str):
        return_cols = [return_cols]
    try:
        # use getattr to avoid having if statements for each operation.
        df = pd.DataFrame(getattr(df.groupby(groupby_cols), type)(numeric_only=True))[
            return_cols
        ]
        if rename_return_cols:
            rename_dict = {}
            for i, val in enumerate(return_cols):
                rename_dict[val] = rename_return_cols[i]
            df = df.rename(columns=rename_dict)
        df = df.reset_index()
    except Exception as e:
        print(e)
        df = pd.DataFrame()
    return df


def get_current_account_balances(
    transactions_df: pd.DataFrame, accounts_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Add column with current account balances to accounts DataFrame by summing all transactions for each account.

    Parameters
    ----------
    transactions_df: pd.DataFrame
        DataFrame with all transactions.

    accounts_df: pd.DataFrame
        DataFrame with all accounts.

    Returns
    -------
    `pd.DataFrame` with new column with current account balance..
    """
    transactions_sum = df_summary(
        transactions_df,
        "transaction_account_id",
        "transaction_amount",
        "total_transaction_amount",
    )
    if len(accounts_df) > 0 and len(transactions_sum) > 0:
        balances_df = accounts_df.merge(
            transactions_sum,
            left_on="account_id",
            right_on="transaction_account_id",
            how="left",
        )
        balances_df["total_transaction_amount"] = balances_df[
            "total_transaction_amount"
        ].fillna(0.00)
        balances_df["current_account_balance"] = (
            balances_df["account_starting_balance"]
            - balances_df["total_transaction_amount"]
        )
    else:
        balances_df = accounts_df
        balances_df[["current_account_balance", "total_transaction_amount"]] = None
    return balances_df


def populate_list(series: pd.Series, values: str | List = ["<New value>"]) -> np.array:
    """
    Add additional values to input pd.Series and return unique items.
    Needed because of streamlit selectbox limitation of not allowing for new typed elements.

    Parameters
    ----------
    series: pd.Series
        Series to append values to.

    values: str | List, default=["<New value>"]
        List of values, or str with single value to append to `series`.

    Returns
    -------
    `np.array` with unique items after appending the inputs.
    """

    return pd.concat([pd.Series(values), series]).unique()


def get_index(row: pd.Series, val: str | int) -> Optional[int]:
    """
    Get index for an element in a pd.Series.

    Parameters
    ----------
    row: pd.Series
        Input Series to lookup value.

    val: str| int
        Value to lookup in `row`.

    Returns
    -------
    `int` with summarized values. `None` if not found or error.
    """
    try:
        ind = np.where(row == val)[0][0]
        return int(ind)
    except Exception:
        return None


@st.dialog("Category Details")
def category_dialog(row: Optional[dict] = None) -> None:
    """
    Create dialog box UI for categories.

    Parameters
    ----------
    row: Optional[dict]
        Optional dictionary with values to pre-fill dialog box fields with. Used while editing existing records.

    Returns
    ----------
    `None`
    """
    if not isinstance(row, dict):
        row = dict()
    with st.container():
        category_logo = st.text_input("Logo", value=row.get("category_logo"),max_chars=1)
        category_name = st.text_input("Category Name", value=row.get("category_name"))
        submit_enabled = category_name
        ### Does not work
        if not category_logo or category_logo == "":
            category_logo = None

        category = pd.DataFrame(
            {"category_logo": [category_logo], "category_name": [category_name]}
        )

        block1 = st.columns(2)
        if row.get("category_id"):
            delete_enabled = (
                False
                if row.get("category_id")
                in st.session_state["detailed_transactions_df"][
                    "transaction_category_id"
                ].unique()
                else True
            )
            if block1[1].button(
                "Update Category",
                disabled=not submit_enabled,
                use_container_width=True,
            ):
                db_operations.table_update(
                    table_name="categories",
                    id_col="category_id",
                    val=row.get("category_id"),
                    df=category,
                )
                # Need to rerun so that option values get updated.
                del (
                    st.session_state["categories_df"],
                    st.session_state["detailed_transactions_df"],
                )
                st.rerun()
            with block1[0].popover(
                "Delete Category", use_container_width=True, disabled=not delete_enabled
            ):
                if st.button(
                    "Delete Category",
                    disabled=not delete_enabled,
                    type="primary",
                    use_container_width=True,
                ):
                    db_operations.table_delete(
                        table_name="categories",
                        id_col="category_id",
                        val=row.get("category_id"),
                    )
                    del st.session_state["categories_df"]
                    st.rerun()
        else:
            if block1[1].button(
                "Add Category", disabled=not submit_enabled, use_container_width=True
            ):
                db_operations.table_insert(table_name="categories", df=category)
                del st.session_state["categories_df"]
                st.rerun()


@st.dialog("Account Details")
def account_dialog(row: Optional[dict] = None) -> None:
    """
    Create dialog box UI for accounts.

    Parameters
    ----------
    row: Optional[dict]
        Optional dictionary with values to pre-fill dialog box fields with. Used while editing existing records.

    Returns
    ----------
    `None`
    """
    if not isinstance(row, dict):
        row = dict()
    with st.container():
        account_name = st.text_input(
            placeholder="ex. BoFA", label="Account Name", value=row.get("account_name")
        )

        block1 = st.columns([8, 1], vertical_alignment="bottom")
        account_type_options = st.session_state["account_types_df"][
            "account_type_name"
        ].sort_values()
        account_type = block1[0].selectbox(
            options=account_type_options,
            label="Type",
            index=(
                get_index(
                    account_type_options,
                    row.get("account_type_name"),
                )
                or 0
            ),
        )
        account_type_details = (
            st.session_state["account_types_df"]
            .loc[
                st.session_state["account_types_df"]["account_type_name"]
                == account_type
            ]
            .iloc[0]
        )
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
                st.rerun()

        block2 = st.columns([4, 5])
        account_currency_options = st.session_state["currencies_df"][
            "currency_abbr"
        ].sort_values()
        account_currency = block2[0].selectbox(
            options=account_currency_options,
            label="Select Account Currency",
            index=get_index(
                account_currency_options,
                row.get("account_currency"),
            ),
        )
        account_starting_balance = block2[1].number_input(
            label="Account Starting Balance",
            value=(row.get("account_starting_balance") or 0.0),
        )

        account_rewards = st.toggle(
            label="Rewards Account?", value=row.get("account_rewards")
        )
        if account_rewards:
            account_currency = "Currency" if not account_currency else account_currency
            rewards_account_type_options = pd.Series(
                ["Points", "Miles", f"{account_currency} Value"]
            )
            rewards_account_type = st.selectbox(
                options=rewards_account_type_options,
                label="Rewards Account Type",
                index=get_index(rewards_account_type_options, row.get("rewards_type")),
            )
            if rewards_account_type == "Points" or rewards_account_type == "Miles":
                point_value = st.number_input(
                    placeholder=f"{account_currency} per {rewards_account_type.rstrip('s')}",
                    label=f"{rewards_account_type} Value",
                    value=(row.get("rewards_point_value") or None),
                )
            else:
                point_value = 1.0
            starting_rewards_balance = st.number_input(
                label="Starting Rewards Balance",
                value=(row.get("starting_rewards_balance") or 0.0),
            )

        submit_enabled = account_name and account_type and account_currency
        if submit_enabled:
            account = pd.DataFrame(
                {
                    "account_name": [account_name],
                    "account_type_id": [account_type_details["account_type_id"]],
                    "account_starting_balance": [account_starting_balance],
                    "account_currency": [account_currency],
                    "account_rewards": [account_rewards],
                    "is_active": [True],
                }
            )
            if account_rewards:
                rewards_account = pd.DataFrame(
                    {
                        "linked_account_id": [None],
                        "rewards_type": [rewards_account_type],
                        "rewards_point_value": [point_value],
                        "starting_rewards_balance": [starting_rewards_balance],
                        "is_active": [True],
                    }
                )
        block3 = st.columns(2)
        if row.get("account_id"):
            button_name = "Edit Account" if row.get("is_active") else "Activate Account"
            if block3[1].button(
                button_name, disabled=not submit_enabled, use_container_width=True
            ):
                db_operations.table_update(
                    table_name="accounts",
                    id_col="account_id",
                    val=row.get("account_id"),
                    df=account,
                )
                if account_rewards and bool(row.get("account_rewards")):
                    rewards_account["linked_account_id"] = row.get("account_id")
                    db_operations.table_update(
                        table_name="rewards_accounts",
                        id_col="rewards_account_id",
                        val=row.get("rewards_account_id"),
                        df=rewards_account,
                    )
                elif account_rewards and not bool(row.get("account_rewards")):
                    rewards_account["linked_account_id"] = row.get("account_id")
                    db_operations.table_insert(
                        table_name="rewards_accounts", df=rewards_account
                    )
                elif not account_rewards and bool(row.get("account_rewards")):
                    deactivate_df = pd.DataFrame({"is_active": [False]})
                    db_operations.table_update(
                        table_name="rewards_accounts",
                        id_col="linked_account_id",
                        val=row.get("account_id"),
                        df=deactivate_df,
                    )
                del (
                    st.session_state["detailed_accounts_df"],
                    st.session_state["detailed_rewards_accounts_df"],
                )
                st.rerun()
            deactivate_enabled = row.get("is_active")
            with block3[0].popover("Deactivate Account", use_container_width=True):
                if st.button(
                    "Deactivate Account",
                    disabled=not deactivate_enabled,
                    use_container_width=True,
                    type="primary",
                ):
                    deactivate_df = pd.DataFrame({"is_active": [False]})
                    db_operations.table_update(
                        table_name="accounts",
                        id_col="account_id",
                        val=row.get("account_id"),
                        df=deactivate_df,
                    )
                    db_operations.table_update(
                        table_name="rewards_accounts",
                        id_col="linked_account_id",
                        val=row.get("account_id"),
                        df=deactivate_df,
                    )
                    del (
                        st.session_state["detailed_accounts_df"],
                        st.session_state["detailed_rewards_accounts_df"],
                    )
                    st.rerun()
        else:
            if block3[1].button(
                "Add Account", disabled=not submit_enabled, use_container_width=True
            ):
                db_operations.table_insert(table_name="accounts", df=account)
                if account_rewards:
                    linked_account_id = db_operations.table_query(
                        f"Select account_id from accounts where account_name='{account_name}'"
                    )["account_id"][0]
                    rewards_account["linked_account_id"] = linked_account_id
                    db_operations.table_insert(
                        table_name="rewards_accounts", df=rewards_account
                    )
                del (
                    st.session_state["detailed_accounts_df"],
                    st.session_state["detailed_rewards_accounts_df"],
                )
                st.rerun()


@st.dialog("Transaction Details", width="large")
def transaction_dialog(row: Optional[dict] = None) -> None:
    """
    Create dialog box UI for transactions.

    Parameters
    ----------
    row: Optional[dict]
        Optional dictionary with values to pre-fill dialog box fields with. Used while editing existing records.

    Returns
    ----------
    `None`
    """
    if not isinstance(row, dict):
        row = dict()

    with st.container():
        block1 = st.columns([3, 3, 2])
        merchant_options = st.session_state["detailed_transactions_df"][
            ~st.session_state["detailed_transactions_df"][
                "transaction_merchant_name"
            ].str.contains("Transfer")
        ]["transaction_merchant_name"]
        final_merchant_options = populate_list(merchant_options.sort_values())
        merchant = block1[0].selectbox(
            "Merchant/Location",
            options=final_merchant_options,
            index=(
                get_index(final_merchant_options, row.get("transaction_merchant_name"))
                or 0
            ),
        )
        # New values cannot be typed in selectbox, thus creating new field.
        if merchant == "<New value>":
            new_merchant = block1[0].text_input("Add new Merchant/Location")
            final_merchant = new_merchant
        else:
            final_merchant = merchant
        account_options = st.session_state["detailed_accounts_df"][
            st.session_state["detailed_accounts_df"]["is_active"] == True
        ]["account_name"].sort_values()
        account_name = block1[1].selectbox(
            "Account",
            options=account_options,
            index=(
                get_index(
                    account_options,
                    row.get("transaction_account_name"),
                )
                or 0
            ),
        )
        account_details = (
            st.session_state["detailed_accounts_df"]
            .loc[
                st.session_state["detailed_accounts_df"]["account_name"] == account_name
            ]
            .iloc[0]
        )
        transaction_date = block1[2].date_input(
            label="Transaction Date", value=(row.get("transaction_date") or "today")
        )

        block2 = st.columns(3)
        category_options = st.session_state["categories_df"][
            "category_name"
        ].sort_values()
        category = block2[0].selectbox(
            "Category",
            options=category_options,
            index=(
                get_index(
                    category_options,
                    row.get("transaction_category_name"),
                )
                or 0
            ),
        )
        category_details = (
            st.session_state["categories_df"]
            .loc[st.session_state["categories_df"]["category_name"] == category]
            .iloc[0]
        )
        sub_category_options = populate_list(
            st.session_state["detailed_transactions_df"][
                "transaction_sub_category"
            ].sort_values()
        )
        sub_category = block2[1].selectbox(
            "Sub Category",
            options=sub_category_options,
            index=get_index(sub_category_options, row.get("transaction_sub_category")),
        )
        # New values cannot be typed in selectbox, thus creating new field.
        if sub_category == "<New value>":
            new_sub_category = block2[1].text_input("Add new Sub Category")
            final_sub_category = new_sub_category
        else:
            final_sub_category = sub_category
        status_options_emoji = pd.Series(["⏳ Pending", "✅ Complete"])
        status_options = pd.Series(["Pending", "Complete"])
        status = block2[2].selectbox(
            "Transaction Status",
            options=status_options_emoji,
            index=(get_index(status_options, row.get("transaction_status")) or 0),
        )
        status = status[2:]

        block3 = st.columns(2)
        transaction_currency = block3[0].selectbox(
            "Currency",
            options=[account_details["account_currency"]],
            index=0,
            disabled=True,
        )
        transaction_amount = block3[0].number_input(
            "Amount", value=(row.get("transaction_amount") or 0.00)
        )
        rewards_enabled = account_details["account_rewards"]
        if rewards_enabled:
            rewards_account_id = (
                st.session_state["detailed_rewards_accounts_df"]
                .loc[
                    st.session_state["detailed_rewards_accounts_df"][
                        "linked_account_id"
                    ]
                    == account_details["account_id"],
                    "rewards_account_id",
                ]
                .iloc[0]
            )
        else:
            rewards_account_id = None
        rewards_percentage = block3[1].number_input(
            "Rewards Percentage (%)",
            value=(row.get("rewards_percentage") or 0.00),
            step=0.5,
            disabled=not rewards_enabled,
        )
        rewards_calculation = round(transaction_amount * (rewards_percentage / 100), 2)
        rewards_amount = block3[1].number_input(
            "Rewards Amount", value=rewards_calculation, disabled=not rewards_enabled
        )
        transaction_total = float(transaction_amount - rewards_amount)

        transaction_notes = st.text_area(
            label="Transaction Notes", value=row.get("transaction_notes")
        )
        submit_enabled = (
            final_merchant
            and account_name
            and transaction_currency
            and category
            and transaction_amount
        )
        if submit_enabled:
            transaction = pd.DataFrame(
                {
                    "transaction_merchant_name": [final_merchant],
                    "transaction_account_id": [account_details["account_id"]],
                    "transaction_date": [transaction_date],
                    "transaction_category_id": [category_details["category_id"]],
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
                    "transaction_status": [status],
                    "transfer_id": [None],
                }
            )
        block4 = st.columns(3)
        if row.get("transaction_id"):
            if block4[2].button(
                "Update Transaction",
                disabled=not submit_enabled,
                use_container_width=True,
            ):
                db_operations.table_update(
                    table_name="cashflow_transactions",
                    id_col="transaction_id",
                    val=row.get("transaction_id"),
                    df=transaction,
                )
                del st.session_state["detailed_transactions_df"]
                st.rerun()
            with block4[0].popover("Delete Transaction", use_container_width=True):
                if st.button(
                    "Delete Transaction",
                    disabled=not submit_enabled,
                    type="primary",
                    use_container_width=True,
                ):
                    db_operations.table_delete(
                        table_name="cashflow_transactions",
                        id_col="transaction_id",
                        val=row.get("transaction_id"),
                    )
                    del st.session_state["detailed_transactions_df"]
                    st.rerun()
        else:
            if block4[2].button(
                "Add Transaction", disabled=not submit_enabled, use_container_width=True
            ):
                db_operations.table_insert(
                    table_name="cashflow_transactions", df=transaction
                )
                del st.session_state["detailed_transactions_df"]
                st.rerun()


@st.dialog("Transfer Details", width="large")
def transfer_dialog(row: Optional[dict] = None) -> None:
    """
    Create dialog box UI to for transfers.

    Parameters
    ----------
    row: Optional[dict]
        Optional dictionary with values to pre-fill dialog box fields with. Used while editing existing records.

    Returns
    ----------
    `None`
    """
    if not isinstance(row, dict):
        row = dict()
    with st.container():
        block1 = st.columns(3)
        origin_account_options = st.session_state["detailed_accounts_df"][
            st.session_state["detailed_accounts_df"]["is_active"] == True
        ]["account_name"].sort_values()
        origin_account = block1[0].selectbox(
            options=origin_account_options,
            label="Origin Account",
            index=(
                get_index(
                    origin_account_options,
                    row.get("origin_account_name"),
                )
                or 0
            ),
        )
        origin_account_details = (
            st.session_state["detailed_accounts_df"]
            .loc[
                st.session_state["detailed_accounts_df"]["account_name"]
                == origin_account
            ]
            .iloc[0]
        )
        destination_account_options = st.session_state["detailed_accounts_df"][
            (st.session_state["detailed_accounts_df"]["account_name"] != origin_account)
            & (st.session_state["detailed_accounts_df"]["is_active"] == True)
        ]["account_name"].sort_values()
        destination_account = block1[1].selectbox(
            options=destination_account_options,
            label="Destination Account",
            index=(
                get_index(
                    destination_account_options, row.get("destination_account_name")
                )
                or 0
            ),
        )
        destination_account_details = (
            st.session_state["detailed_accounts_df"]
            .loc[
                st.session_state["detailed_accounts_df"]["account_name"]
                == destination_account
            ]
            .iloc[0]
        )
        transfer_date = block1[2].date_input(
            label="Transfer Date", value=(row.get("transfer_date") or "today")
        )

        block2 = st.columns([4, 4])
        origin_transfer_charges = block2[0].number_input(
            label="Origin Transfer Charges",
            value=(row.get("origin_transfer_charges") or 0.00),
        )
        destination_transfer_charges = block2[1].number_input(
            label="Destination Transfer Charges",
            value=(row.get("destination_transfer_charges") or 0.00),
        )

        conversion_rate = 1.0
        if isinstance(origin_account, str) & isinstance(destination_account, str):
            if (
                origin_account_details["account_currency"]
                != destination_account_details["account_currency"]
            ):
                block3 = st.columns([4, 4, 4])
                origin_currency = block3[0].selectbox(
                    options=origin_account_details["account_currency"],
                    index=0,
                    label="Origin Currency",
                    disabled=True,
                )
                destination_currency = block3[1].selectbox(
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
                conversion_rate = block3[2].number_input(
                    label="Conversion Rate",
                    value=(
                        row.get("currency_conversion_rate")
                        or conversion_rate_value
                        or 0.00
                    ),
                    format="%.6f",
                )
            else:
                origin_currency = destination_currency = origin_account_details[
                    "account_currency"
                ]

        block4 = st.columns(2)
        send_amount = block4[0].number_input(
            label="Send Amount", value=(row.get("origin_send_amount") or 0.00)
        )
        received_amount_calc = (
            send_amount * conversion_rate
        ) - destination_transfer_charges
        received_amount = block4[1].number_input(
            label="Received Amount", value=received_amount_calc
        )
        transfer_notes = st.text_area(
            label="Transfer Notes", value=row.get("transfer_notes")
        )

        submit_enabled = (
            origin_account and destination_account and transfer_date and send_amount
        )
        if submit_enabled:
            category_id = (
                st.session_state["categories_df"]
                .loc[
                    st.session_state["categories_df"]["category_name"]
                    == "Account Transfer",
                    "category_id",
                ]
                .iloc[0]
            )
            transfer = pd.DataFrame(
                {
                    "transfer_date": [transfer_date],
                    "origin_account_id": [origin_account_details["account_id"]],
                    "destination_account_id": [
                        destination_account_details["account_id"]
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
            transactions = pd.DataFrame(
                {
                    "transaction_merchant_name": [
                        f"{origin_account} -> {destination_account} Transfer"
                    ]
                    * 2,
                    "transaction_account_id": [
                        origin_account_details["account_id"],
                        destination_account_details["account_id"],
                    ],
                    "transaction_date": [transfer_date] * 2,
                    "transaction_category_id": [category_id] * 2,
                    "transaction_sub_category": [None] * 2,
                    "transaction_currency": [origin_currency, destination_currency],
                    "transaction_amount": [
                        send_amount + origin_transfer_charges,
                        -(received_amount - destination_transfer_charges),
                    ],
                    "rewards_account_id": [None] * 2,
                    "rewards_percentage": [0.00] * 2,
                    "rewards_amount": [0.00] * 2,
                    "transaction_total": [
                        send_amount + origin_transfer_charges,
                        -(received_amount - destination_transfer_charges),
                    ],
                    "transaction_notes": [transfer_notes] * 2,
                    "transaction_status": ["Complete"] * 2,
                    "transfer_id": [row.get("transfer_id")] * 2,
                }
            )
        block5 = st.columns(3)
        if row.get("transfer_id"):
            if block5[2].button(
                "Update Transfer",
                disabled=not submit_enabled,
                use_container_width=True,
            ):
                db_operations.table_update(
                    table_name="cashflow_transfers",
                    id_col="transfer_id",
                    val=row.get("transfer_id"),
                    df=transfer,
                )
                db_operations.table_update(
                    table_name="cashflow_transactions",
                    id_col=["transaction_account_id", "transfer_id"],
                    val=[row.get("origin_account_id"), row.get("transfer_id")],
                    df=transactions.loc[0:0],
                )
                db_operations.table_update(
                    table_name="cashflow_transactions",
                    id_col=["transaction_account_id", "transfer_id"],
                    val=[row.get("destination_account_id"), row.get("transfer_id")],
                    df=transactions.loc[1:1],
                )
                del (
                    st.session_state["detailed_transactions_df"],
                    st.session_state["detailed_transfers_df"],
                )
                st.rerun()
            with block5[0].popover("Delete Transfer", use_container_width=True):
                if st.button(
                    "Delete Transfer",
                    disabled=not submit_enabled,
                    type="primary",
                    use_container_width=True,
                ):
                    db_operations.table_delete(
                        table_name="cashflow_transfers",
                        id_col="transfer_id",
                        val=row.get("transfer_id"),
                    )
                    db_operations.table_delete(
                        table_name="cashflow_transactions",
                        id_col="transfer_id",
                        val=row.get("transfer_id"),
                    )
                    del (
                        st.session_state["detailed_transactions_df"],
                        st.session_state["detailed_transfers_df"],
                    )
                    st.rerun()
        else:
            if block5[2].button(
                "Add Transfer", disabled=not submit_enabled, use_container_width=True
            ):
                db_operations.table_insert(table_name="cashflow_transfers", df=transfer)
                transfer_id = db_operations.table_query(
                    "Select max(transfer_id) as transfer_id from cashflow_transfers"
                )["transfer_id"][0]
                transactions["transfer_id"] = [transfer_id] * 2
                db_operations.table_insert(
                    table_name="cashflow_transactions", df=transactions
                )
                del (
                    st.session_state["detailed_transactions_df"],
                    st.session_state["detailed_transfers_df"],
                )
                st.rerun()


def split_frame(df: pd.DataFrame, current_page: int, max_per_page: int) -> pd.DataFrame:
    """
    Paginate input dataframe based on input params.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame to paginate.

    current_page: int
        Page offset for paginated output.

    max_per_page: int
        Page size for paginated output.

    Returns
    ----------
    `pd.DataFrame` with paginated output.
    """
    return df.loc[
        ((current_page - 1) * max_per_page) : ((current_page - 1) * max_per_page)
        + max_per_page
        - 1
    ]


def display_filter_ui(type: str) -> filterArgs:
    """
    Display UI with filters.

    Parameters
    ----------
    type: str, ["transaction_filters","transfer_filters","account_filters"]
        Filter type based on section.

    Returns
    ----------
    `filterArgs` dict with filter values.
    """
    filters = st.expander("Filters", icon=":material/filter_alt:", expanded=True)
    filter_args: filterArgs = {}
    if type == "transaction_filters":
        filter_block1 = filters.columns(5)
        filter_block2 = filters.columns(5)
        account_types_filter = filter_block1[0].multiselect(
            label="Account Types",
            options=st.session_state["detailed_accounts_df"]["account_type_name"]
            .sort_values()
            .unique(),
        )
        accounts_filter = filter_block1[1].multiselect(
            label="Account Name",
            options=st.session_state["detailed_accounts_df"]["account_name"]
            .sort_values()
            .unique(),
        )
        date_filter = filter_block1[2].selectbox(
            label="Date Range",
            options=["Current Month", "Last 30 Days", "Last 365 Days", "YTD", "Custom"],
        )
        if date_filter == "Custom":
            start_date_filter = pd.to_datetime(
                filter_block1[1].date_input(label="Start Date", value="today")
            )
            end_date_filter = pd.to_datetime(
                filter_block1[2].date_input(
                    label="End Date", value="today", min_value=start_date_filter
                )
            )
        elif date_filter == "Current Month":
            start_date_filter, end_date_filter = datetime(
                today.year, today.month, 1
            ), datetime(today.year, today.month, 1) + pd.offsets.MonthEnd(1)
        elif date_filter == "Last 30 Days":
            start_date_filter, end_date_filter = today - timedelta(30), today
        elif date_filter == "Last 365 Days":
            start_date_filter, end_date_filter = today - timedelta(365), today
        elif date_filter == "YTD":
            start_date_filter, end_date_filter = datetime(today.year, 1, 1), today
        categories_types_filter = filter_block1[3].multiselect(
            label="Categories",
            options=st.session_state["categories_df"]["category_name"]
            .sort_values()
            .unique(),
        )
        transaction_status_filter = filter_block1[4].multiselect(
            label="Transaction Status",
            options=["Complete", "Pending"],
            default=None,
        )

        include_transfers = filter_block2[0].checkbox(
            label="Include Transfers", value=True
        )
        include_inflow = filter_block2[1].checkbox(label="Include Income", value=True)

        filter_args: filterArgs = {
            "account_types_filter": account_types_filter,
            "accounts_filter": accounts_filter,
            "date_filter": (start_date_filter, end_date_filter),
            "categories_types_filter": categories_types_filter,
            "transaction_status_filter": transaction_status_filter,
            "transfers_filter": include_transfers,
            "inflow_filter": include_inflow,
            "cumulative_calculation": False,
        }
    elif type == "transfer_filters":
        filter_block1 = filters.columns(3)
        origin_account_filter = filter_block1[0].multiselect(
            label="Origin Account",
            options=st.session_state["detailed_accounts_df"]["account_name"]
            .sort_values()
            .unique(),
        )
        destination_account_filter = filter_block1[1].multiselect(
            label="Destination Account",
            options=st.session_state["detailed_accounts_df"]["account_name"]
            .sort_values()
            .unique(),
        )
        date_filter = filter_block1[2].selectbox(
            label="Date Range",
            options=["Current Month", "Last 30 Days", "Last 365 Days", "YTD", "Custom"],
        )
        if date_filter == "Custom":
            start_date_filter = pd.to_datetime(
                filter_block1[1].date_input(label="Start Date", value="today")
            )
            end_date_filter = pd.to_datetime(
                filter_block1[2].date_input(
                    label="End Date", value="today", min_value=start_date_filter
                )
            )
        elif date_filter == "Current Month":
            start_date_filter, end_date_filter = datetime(
                today.year, today.month, 1
            ), datetime(today.year, today.month, 1) + pd.offsets.MonthEnd(1)
        elif date_filter == "Last 30 Days":
            start_date_filter, end_date_filter = today - timedelta(30), today
        elif date_filter == "Last 365 Days":
            start_date_filter, end_date_filter = today - timedelta(365), today
        elif date_filter == "YTD":
            start_date_filter, end_date_filter = datetime(today.year, 1, 1), today

        filter_args: filterArgs = {
            "origin_account_filter": origin_account_filter,
            "destination_account_filter": destination_account_filter,
            "date_filter": (start_date_filter, end_date_filter),
        }
    elif type == "account_filters":
        filter_block1 = filters.columns(4, vertical_alignment="bottom")
        account_types_filter = filter_block1[0].multiselect(
            label="Account Types",
            options=st.session_state["detailed_accounts_df"]["account_type_name"]
            .sort_values()
            .unique(),
        )
        account_currency_filter = filter_block1[1].multiselect(
            label="Account Currency",
            options=st.session_state["detailed_accounts_df"]["account_currency"]
            .sort_values()
            .unique(),
        )
        account_rewards_filter = filter_block1[2].multiselect(
            label="Account Rewards",
            options=[True, False],
        )
        is_active_filter = filter_block1[3].checkbox(label="Show inactive accounts?")
        filter_args: filterArgs = {
            "account_types_filter": account_types_filter,
            "account_currency_filter": account_currency_filter,
            "account_rewards_filter": account_rewards_filter,
            "is_active_filter": not is_active_filter,
        }
    return filter_args


def display_card_ui(
    display_df: pd.DataFrame, type: str, default_page_size: int = 10
) -> None:
    """
    Display UI with cards.

    Parameters
    ----------
    display_df: pd.DataFrame
        Input DataFrame to iterate through and create Card UI.

    type: str, ["transactions","categories","transfers","accounts"]
        Card UI type based on section.

    default_page_size: int, default=10
        Default page size for number of cards to display per page.
    """

    block = st.columns(2)
    left_con = block[0].container()
    right_con = block[1].container()
    bottom_menu = st.columns([3, 1, 1])

    page_size_options = pd.Series([10, 25, 50])
    max_per_page = bottom_menu[1].selectbox(
        label="Per Page",
        options=page_size_options,
        index=get_index(page_size_options, default_page_size),
        key=f"max_per_page_{type}",
    )
    total_pages = (
        math.ceil(len(display_df) / max_per_page)
        if int(len(display_df) / max_per_page) > 0
        else 1
    )
    current_page = bottom_menu[2].number_input(
        "Page", min_value=1, max_value=total_pages, step=1, key=f"current_page_{type}"
    )
    for row in split_frame(
        display_df.reset_index(drop=True),
        current_page,
        max_per_page,
    ).itertuples():
        con = None
        if getattr(row, "Index") % 2 == 0:
            con = left_con.container(border=True)
        else:
            con = right_con.container(border=True)

        if type == "transactions":
            line0 = con.columns([1, 7, 5, 1], vertical_alignment="center")
            line1 = con.columns([4, 5, 1], vertical_alignment="center")
            line0[1].markdown(row.transaction_merchant_name)
            line0[2].markdown((row.transaction_date).strftime("%b %d %Y"))

            edit_disable = not np.isnan(row.transfer_id)
            line0[3].button(
                "✎",
                key=f"edit_transaction_{row.transaction_id}",
                on_click=transaction_dialog,
                args=[row._asdict()],
                use_container_width=True,
                disabled=edit_disable,
            )

            line0[0].markdown(
                row.transaction_category_logo,
            )
            if row.transaction_notes:
                line1[0].text_area(
                    label=f"notes_{row.transaction_id}",
                    value=row.transaction_notes,
                    label_visibility="collapsed",
                    height=10,
                    max_chars=20,
                    disabled=True,
                )
            line1[1].metric(
                label=f"{row.transaction_account_name}",
                value=format_currency(
                    row.transaction_amount, row.transaction_currency, locale="en_US"
                ),
            )
            status_icon = "⏳" if row.transaction_status == "Pending" else "✅"
            line1[2].text(status_icon)
        elif type == "categories":
            line0 = con.columns([2, 8, 1], vertical_alignment="center")
            if row.category_logo:
                line0[0].markdown(row.category_logo)
            line0[1].markdown(row.category_name)
            line0[2].button(
                "✎",
                key=f"edit_category_{row.category_id}",
                on_click=category_dialog,
                args=[row._asdict()],
                use_container_width=True,
            )
        elif type == "transfers":
            line0 = con.columns([8, 4, 1], vertical_alignment="center")
            line1 = con.columns(2, vertical_alignment="center")
            line0[0].markdown(
                f"{row.origin_account_name} -> {row.destination_account_name}"
            )
            line0[1].markdown((row.transfer_date).strftime("%b %d %Y"))
            line0[2].button(
                "✎",
                key=f"edit_transfer_{row.transfer_id}",
                on_click=transfer_dialog,
                args=[row._asdict()],
                use_container_width=True,
            )

            line1[0].metric(
                label="Sent Amount",
                value=format_currency(
                    (row.origin_send_amount + row.origin_transfer_charges),
                    row.origin_currency,
                    locale="en_US",
                ),
            )
            line1[1].metric(
                label="Received Amount",
                value=format_currency(
                    (
                        row.destination_received_amount
                        - row.destination_transfer_charges
                    ),
                    row.destination_currency,
                    locale="en_US",
                ),
            )
        elif type == "accounts":
            line0 = con.columns([7, 4, 1], vertical_alignment="bottom")
            line0[0].subheader(row.account_name, anchor=False)
            line0[2].button(
                "✎",
                key=f"edit_account_{row.account_id}",
                on_click=account_dialog,
                args=[row._asdict()],
                use_container_width=True,
            )

            line0[1].markdown(
                f":gray-background[:blue[{row.account_type_name}]]",
            )
            con.metric(
                "Current Balance",
                format_currency(
                    row.current_account_balance, row.account_currency, locale="en_US"
                ),
            )


curr = Currencies(db_operations)
