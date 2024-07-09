from sqlalchemy.sql import text
from sqlalchemy import create_engine
import json
import toml
import pandas as pd
from typing import Optional


class ConnectDB:
    def __init__(self, db_name:str) -> None:
        """
        Initializes class with creating SQLAlchemy engine and db_config dict.

        Parameters
        ----------
        db_name : str
            Name of database as in toml config.

        Returns
        ----------
        `None`
        """
        self.source_dict = toml.load(".streamlit/secrets.toml")["connections"][db_name]
        if "url" in self.source_dict:
            self.engine = create_engine(self.source_dict["url"])
        self.db_config_path = "files/db_config.json"
        with open(self.db_config_path) as f:
            self.db_config_dict = json.load(f)

    def raw_query(self, query:str) -> bool:
        """
        Utilize SQLAlchemy engine to execute a query on the database. 
        Does not return output, use `table_query()` if response output is required.

        Parameters
        ----------
        query : str
            Query string to execute on the database.

        Returns
        -------
        `True` if query successfully executed, `False` otherwise.
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(text(query))
                connection.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def table_create(self, table_name:str) -> bool:
        """
        Create a table it doesn't exist in the database using field definitions from `self.db_config_dict`.

        Parameters
        ----------
        table_name : str
            Name of table to create in database.

        Returns
        -------
        `True` if table is created successfully, `False` otherwise.
        """
        try:
            table_config = self.db_config_dict["databases"][table_name]
            column_config = (
                "("
                + ", ".join([(f"{id} {val}") for id, val in table_config.items()])
                + ");"
            )
            result = self.raw_query(f"CREATE TABLE IF NOT EXISTS {table_name} {column_config}")
            return result
        except Exception as e:
            print(e)
            return False

    def table_delete(self, table_name:str) -> bool:
        """
        Delete a table if it exists in the database. 

        Parameters
        ----------
        table_name : str
            Name of table to delete in database.

        Returns
        -------
       `True` if table is deleted successfully, `False` otherwise.
        """
        try:
            result = self.raw_query(f"DROP VIEW IF EXISTS {table_name}")
            return result
        except Exception as e:
            print(e)
            return False

    def table_query(self, query:str) -> Optional[pd.DataFrame]:
        """
        Utilize pandas.read_sql_query to execute a query on the database and return output as a DataFrame. 
        Use `raw_query()` if DDL operations need to be performed on the database.

        Parameters
        ----------
        query : str
            Query string to execute on the database.

        Returns
        -------
        `pd.DataFrame` with query results, `None` if any errors.
        """
        try:
            results = pd.read_sql_query(query, con=self.engine)
            return results
        except Exception as e:
            print(e)
            return None
    
    def table_exists(self, table_name:str) -> bool:
        """
        Check if table exists in the database.

        Parameters
        ----------
        table_name : str
            Name of table to check in the database.

        Returns
        -------
        `True` if table exists, `False` otherwise.
        """
        out = self.table_query(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if len(out)> 0:
            return True
        else:
            return False
    
    def table_insert(self, table_name: str, df:pd.DataFrame, if_exists:str="append") -> bool:
        """
        Utilize pandas.to_sql to insert values into a table in the database. 

        Parameters
        ----------
        table_name : str
            Name of table to insert values into the database.

        df : pd.DataFrame
            Dataframe with values to insert.
            
        if_exists : str, default="append"
            Query string to execute on the database.

        Returns
        -------
        `True` if insert is successful executed, `False` if errors.
        """
        try:
            df.to_sql(
                name=table_name, if_exists=if_exists, con=self.engine, index=False
            )
            return True
        except Exception as e:
            print(e)
            return False

    def insert_initial_values(self, table_name:str) -> Optional[bool]:
        """
        Insert values from `self.db_config_dict` into a table on the database. 

        Parameters
        ----------
        table_name : str
            Name of table to insert values into the database.

        Returns
        -------
        `True` if insert is successful executed, `False` if errors. `None` if initial dataFrame is empty.
        """
        try:
            df = pd.DataFrame.from_dict(
                self.db_config_dict["initial_values"][table_name]
            )
        except Exception as e:
            print(e)
            return False
        if len(df) > 0:
            result = self.table_insert(table_name, df)
            return result
        else:
            return None

    def create_table_trigger(self, table_name:str, log_table:str="event_logs") -> bool:
        """
        Create INSERT, UPDATE and DELETE table triggers in the database.
        Uses `self.db_config_dict` config to get trigger definition for specified table_name.

        Parameters
        ----------
        table_name : str
            Name of table to create the trigger on in the database.
        
        log_table : str, default="event_logs"
            Name of event log table in the database to store results of trigger operations.
        
        Returns
        -------
        `True` if triggers are created successfully, `False` otherwise.
        """
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
                    check = self.table_query(f"select * from sqlite_master where name='{event.lower()}_event_{table_name}' and type='trigger'")   
                    if len(check) > 0:
                        self.raw_query(trigger_delete_string)
                    self.raw_query(trigger_create_string)
                except Exception as e:
                    print(e)
                    return False
            return True
        except Exception as e:
            print(e)
            return False

    def create_table_view(self, view_name:str) -> bool:
        """
        Create a table view in the database, delete if it already exists in the database. 
        Uses `self.db_config_dict` config to get view definition for specified view_name.

        Parameters
        ----------
        view_name : str
            Name of view to create in database.

        Returns
        -------
        `True` if view is created successfully, `False` otherwise.
        """
        try:
            res1 = self.raw_query(f"DROP VIEW IF EXISTS {view_name}")
            res2 = self.raw_query(self.db_config_dict["views"][view_name])
            return True if all((res1, res2)) else False
        except Exception as e:
            print(e)
            return False            
