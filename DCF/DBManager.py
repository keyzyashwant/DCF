import sqlite3
import pandas as pd
from datetime import datetime

class DataBaseManager:
  def __init__(self, db_path):
    self.db_path = db_path
    self._create_tables()

  def _create_tables(self):
    con = sqlite3.connect(self.db_path)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ratios (
    ticker      TEXT,
    category    TEXT,
    metric      TEXT,
    value       REAL,
    timestamp   TEXT
    )
                """)
    cur.execute("""CREATE TABLE IF NOT EXISTS dcf_summary (
    ticker      TEXT,
    metric      TEXT,
    value       REAL,
    timestamp   TEXT
    )""")

    con.commit()
    con.close()

  def store_ratios(self, ticker, category , df: pd.DataFrame, timestamp):
    
    con = sqlite3.connect(self.db_path)
    cur = con.cursor()

    for each_column in df.columns:
      for each_year in df.index:
        cur.execute(" INSERT INTO ratios VALUES (?,?,?,?,?)", (ticker, category, each_column, df.loc[each_year][each_column], timestamp))
    
    con.commit()
    con.close()

  def store_dcf_summary(self, ticker, dcf_df: pd.DataFrame):
    timestamp = datetime.now().isoformat()
    con = sqlite3.connect(self.db_path)
    cur = con.cursor()

    for each_metric in ['Intrinsic Price', 'Lower Band', 'Upper Band']:
      value = dcf_df.loc[each_metric]['PV (Calculated)']
      cur.execute("INSERT INTO dcf_summary VALUES(?,?,?,?)", (ticker, each_metric, value, timestamp))

    con.commit()
    con.close()

  def get_ratios(self, ticker) -> dict:
    con = sqlite3.connect(self.db_path)
    

    res = " SELECT * FROM ratios WHERE ticker=? AND timestamp = (SELECT MAX(timestamp) FROM ratios WHERE ticker=?)"
    ratios_df = pd.read_sql_query( sql=res, con= con, params=(ticker, ticker))

    profitabolity_df = ratios_df[ratios_df['category'] == 'profitability'][['metric', 'value']].set_index('metric')
    leverage_df = ratios_df[ratios_df['category'] == 'leverage'][['metric', 'value']].set_index('metric')
    operating_df = ratios_df[ratios_df['category'] == 'operating'][['metric', 'value']].set_index('metric')
    valuation_df = ratios_df[ratios_df['category'] == 'valuation'][['metric', 'value']].set_index('metric')

    result = {
      "PROFITABILITY_RATIOS" : profitabolity_df,
      "LEVERAGE_RATIOS": leverage_df,
      "OPERATING_RATIOS": operating_df,
      "VALUATION_RATIOS": valuation_df,
    }
    con.close()

    return result


  def get_dcf_summary(self,ticker) -> pd.DataFrame:
    con = sqlite3.connect(self.db_path)

    res = "SELECT * FROM dcf_summary WHERE ticker=? AND timestamp = (SELECT MAX(timestamp) FROM dcf_summary WHERE ticker=?)"
    dcf_df = pd.read_sql_query(sql= res, con= con, params=(ticker,ticker))
    con.close()
    return dcf_df
    