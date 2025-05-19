from sqlalchemy import create_engine, inspect
import pandas as pd
from pathlib import Path


def checkSql( sqliteFilePath ):
    """
    Task: Outputs the name of all the tables present in the database .sqlite file
            to get an idea of what is the content of the specific file.
    """
    # Step 1: Create an SQLAlchemy engine to connect to the SQLite database
    engine = create_engine(f"sqlite:///{sqliteFilePath}")

    # Step 2: Inspect the database to see available tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("Tables in the database:")
    print(tables)
    print( f"\nExpected Tables: {['mainTable', 'panddaTable', 'collectionTable', 'depositTable','soakDB', 'zenodoTable','Pucks', ]}")

    return tables

def loadDatabase( sqliteFilePath ):
    """
    Task: Convert an sqlite set of tables into a dictionary of pandas dataframes.
    Return
    - { "table1": pd.Dataframe, ... }
    """
    tablesOfInterest = ['mainTable', 'panddaTable', 'collectionTable', 'depositTable',] # These tables contain the information of interest
    setOfInterest = set( tablesOfInterest )


    # Step 1: Create an SQLAlchemy engine to connect to the SQLite database
    engine = create_engine(f"sqlite:///{sqliteFilePath}")

    # Step 2: Inspect the database to see available tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    setOfTables = set( tables )

    # Step 3: Filter from existing tables, those of interest
    setTablesofInterestPresent = setOfInterest.intersection( setOfTables )
    presentTablesofInterest = [ table for table in tablesOfInterest if table in list( setTablesofInterestPresent ) ]

    # Step 4: Load a specific table into a pandas DataFrame
    loadtable = lambda table_name : pd.read_sql(f"SELECT * FROM {table_name}", con=engine)
    tabledf_dict = {table_name : loadtable(table_name) for table_name in presentTablesofInterest }

    engine.dispose()

    return tabledf_dict