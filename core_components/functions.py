import requests
import numpy as np
import pandas as pd
import json


def populate_list(col_name, df):
    try:
        column_list = df[col_name].unique()
    except Exception:
        column_list = np.array([])

    list_values = np.append(column_list, ["<New value>"])

    return list_values


class Currencies:
    def __init__(self, db_operations) -> None:
        self.api_endpoint = "https://open.er-api.com/v6/latest/USD"
        self.db_operations = db_operations

    def get_base_currency(self, table_name="currencies"):
        try:
            base_currency = self.db_operations.table_query(
                f"Select currency_abbr from {table_name} where is_base_currency IS TRUE"
            )["currency_abbr"][0]
            return base_currency
        except Exception as e:
            print(e)
            return None

    def get_currency_rates(self, table_name="currency_rates"):
        try:
            currency_rates = self.db_operations.table_query(
                f"Select * from {table_name}"
            )
            return currency_rates
        except Exception as e:
            print(e)
            return None

    def get_new_currency_rates(self, new_rates=None):
        if not isinstance(new_rates, dict):
            new_rates = json.loads(requests.get(self.api_endpoint).text)
        df = (
            pd.DataFrame.from_dict(new_rates["rates"], orient="index")
            .reset_index()
            .rename(columns={"index": "currency_abbr", 0: "currency_rate"})
        )
        df[["base_currency", "currency_update_timestamp"]] = [
            "USD",
            new_rates["time_last_update_unix"],
        ]
        return df

    def update_currency_rates(self, df, table_name="currency_rates") -> bool:
        try:
            self.db_operations.raw_query(f"DELETE FROM {table_name}")
            self.db_operations.table_insert(
                table_name=table_name, df=df, if_exists="append"
            )
            return True
        except Exception as e:
            print(e)
            return False

    def update_currency_desc(self, df, table_name="currencies") -> bool:
        base_currency = self.get_base_currency()
        df = pd.DataFrame(df)
        df[["currency_symbol", "currency_description", "is_base_currency"]] = [
            "",
            "",
            False,
        ]
        df.loc[df["currency_abbr"] == (base_currency or "USD"), "is_base_currency"] = (
            True
        )
        try:
            self.db_operations.table_insert(
                table_name=table_name, df=df, if_exists="replace"
            )
            return True
        except Exception as e:
            print(e)
            return False

    def check_and_update_currency_rates(self):
        new_rates = json.loads(requests.get(self.api_endpoint).text)
        if new_rates["result"] == "success":
            new_timestamp = new_rates["time_last_update_unix"]
            try:
                current_timestamp_query = "Select max(currency_update_timestamp) as current_timestamp from currency_rates"
                current_timestamp = self.db_operations.query_table(
                    current_timestamp_query
                )["current_timestamp"][0]
            except Exception:
                current_timestamp = 0
            if new_timestamp > (current_timestamp or 0):
                new_rates_df = self.get_new_currency_rates(new_rates)
                self.update_currency_desc(new_rates_df["currency_abbr"])
                self.update_currency_rates(new_rates_df)
        else:
            print("Error response from API, aborting")
            return False

    def get_currency_conversion_rate(
        self, origin_currency, target_currency, currency_rates_df=None
    ):
        try:
            if not isinstance(currency_rates_df, pd.DataFrame):
                currency_rates_df = self.get_currency_rates()

            origin_currency_details = currency_rates_df[
                currency_rates_df["currency_abbr"] == origin_currency
            ].reset_index(drop=True)
            base_currency_details = currency_rates_df[
                currency_rates_df["currency_abbr"] == "USD"
            ].reset_index(drop=True)
            target_currency_details = currency_rates_df[
                currency_rates_df["currency_abbr"] == target_currency
            ].reset_index(drop=True)
            origin_to_base_rate = (
                base_currency_details["currency_rate"][0]
                / origin_currency_details["currency_rate"][0]
            )
            origin_to_target_rate = (
                origin_to_base_rate * target_currency_details["currency_rate"][0]
            )

            return origin_to_target_rate
        except Exception as e:
            print(e)
            return 0.00
