from sqlalchemy.sql import text
from sqlalchemy import create_engine
import json
import toml
import pandas as pd


class ConnectDB:
    def __init__(self, db_name) -> None:
        self.source_dict = toml.load(".streamlit/secrets.toml")["connections"][db_name]
        if "url" in self.source_dict:
            self.engine = create_engine(self.source_dict["url"])
        self.db_config_path = "files/db_config.json"
        with open(self.db_config_path) as f:
            self.db_config_dict = json.load(f)

    def raw_query(self, query) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text(query))
                connection.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def table_create(self, table_name) -> bool:
        try:
            table_config = self.db_config_dict["databases"][table_name]
            column_config = (
                "("
                + ", ".join([(f"{id} {val}") for id, val in table_config.items()])
                + ");"
            )
            with self.engine.connect() as connection:
                connection.execute(
                    text(f"CREATE TABLE IF NOT EXISTS {table_name} {column_config}")
                )
                connection.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def table_insert(self, table_name, df, if_exists="append") -> bool:
        try:
            df.to_sql(
                name=table_name, if_exists=if_exists, con=self.engine, index=False
            )
            return True
        except Exception as e:
            print(e)
            return False

    def table_delete(self, table_name) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                connection.commit()
            return True

        except Exception as e:
            print(e)
            return False

    def table_query(self, query):
        try:
            results = pd.read_sql_query(query, con=self.engine)
            return results
        except Exception as e:
            print(e)
            return None

    def table_exists(self, table_name) -> bool:
        if (
            len(
                self.table_query(
                    f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
                )
            )
            > 0
        ):
            return True
        else:
            return False

    def insert_initial_values(self, table_name):
        try:
            df = pd.DataFrame.from_dict(
                self.db_config_dict["initial_values"][table_name]
            )
        except Exception as e:
            print(e)
            return False
        if len(df) > 0:
            self.table_insert(table_name, df)
        return True

    def create_table_trigger(self, table_name, log_table="event_logs") -> bool:
        try:
            id_field = self.db_config_dict["triggers"][table_name]["id_field"]
            for event in ["INSERT", "UPDATE", "DELETE"]:
                id_reference = "old" if event == "DELETE" else "new"
                trigger_delete_string = (
                    f"DROP TRIGGER {event.lower()}_event_{table_name}"
                )
                trigger_create_string = f"""CREATE TRIGGER {event.lower()}_event_{table_name}
                AFTER {event} ON {table_name}
                BEGIN
                INSERT INTO {log_table} (event_table, event_foreign_key, event_type) VALUES ('{table_name}', {id_reference}.{id_field}, '{event}');
                END;"""
                try:
                    if (
                        len(
                            self.table_query(
                                f"select * from sqlite_master where name='{event.lower()}_event_{table_name}' and type='trigger'"
                            )
                        )
                        > 0
                    ):
                        self.raw_query(trigger_delete_string)
                    self.raw_query(trigger_create_string)
                except Exception as e:
                    print(e)
                    return False
            return True
        except Exception as e:
            print(e)
            return False

    def create_table_view(self, view_name) -> bool:
        try:
            self.raw_query(f"DROP VIEW IF EXISTS {view_name}")
            self.raw_query(self.db_config_dict["views"][view_name])
            return True
        except Exception as e:
            print(e)
            return False

    def table_create_if_missing(self, table_name):
        if not self.table_exists(table_name):
            self.table_create(table_name)
            self.create_table_trigger(table_name)
            self.insert_initial_values(table_name)
