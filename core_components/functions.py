import requests
import numpy as np
import pandas as pd
import json
from typing import List, Optional, Dict
from core_components.database import ConnectDB


def populate_list(series: pd.Series, values: str | List = ["<New value>"]) -> np.array:
    """
    Add additional values to input pd.Series and return unique items.
    Needed because of streamlit selectbox limitation of not allowing for new typed elements.

    Parameters
    ----------
    series : pd.Series
        Series to append values to.

    values : str | List, default=["<New value>"]
        List of values, or str with single value to append.

    Returns
    -------
    `np.array` with unique items after appending the inputs.
    """

    return pd.concat([series, pd.Series(values)]).unique()


class Currencies:
    def __init__(self, db_operations: ConnectDB) -> None:
        """
        Initializes class with database connection and api endpoint.

        Parameters
        ----------
        db_operations : ConnectDB
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
        table_name : str, default="currencies"
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
        df : pd.DataFrame
            DataFrame containing values to update the database table.

        table_name : str, default="currency_rates"
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
        Update currency description stored in the database. (placeholder empty values, to be updated)

        Parameters
        ----------
        df : pd.Series
            Series containing currency abbreviations to update the database table.

        table_name : str, default="currencies"
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
        if new_rates_df["currency_update_timestamp"][0] > current_timestamp:
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
        origin_currency : str
            Origin currency abbreviation.

        target_currency : str
            Target currency abbreviation.

        currency_rates_df : Optional[pd.DataFrame], default=None
            Optional DataFrame to use for currency rate calculations, queries the database otherwise.

        table_name : Optional[str], default="currency_rates"
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
