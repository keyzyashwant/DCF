import yfinance as yf
import pandas as pd

class InvalidTickerError(Exception):
  print("INVALID TICKER")

class MissingDataError(Exception):
  print("MISSING DATA")

class FinancialCollector:
  def __init__(self,symbol : str):
    if not symbol:
      raise InvalidTickerError("You did not type anything")
    
    self.ticker = yf.Ticker(symbol)
    
    if self.ticker.info.get('symbol') is None:
      raise InvalidTickerError("The Code of the ticker is Invalid")
    

  #private method
  def _clean_df(self, raw_df: pd.DataFrame) -> pd.DataFrame:
    raw_df = raw_df.transpose()
    raw_df.index = raw_df.index.year
    return raw_df
    

  def get_p_and_l(self) -> pd.DataFrame:
    raw_df = self.ticker.financials
    if raw_df.empty:
      raise MissingDataError("The data corresponding to this ticker is missing")
    updated_df = self._clean_df(raw_df)
    return updated_df
    

  def get_balance_sheet(self) -> pd.DataFrame:
    raw_df = self.ticker.balance_sheet
    if raw_df.empty:
      raise MissingDataError("The data corresponding to this ticker is missing")
    updated_df = self._clean_df(raw_df)
    return updated_df

  def get_cash_flow(self) -> pd.DataFrame:
    raw_df = self.ticker.cash_flow
    if raw_df.empty:
      raise MissingDataError("The data corresponding to this ticker is missing")
    updated_df = self._clean_df(raw_df)
    return updated_df
  
  def get_info(self) -> dict:
    raw_df = self.ticker.info
    if not raw_df:
      raise MissingDataError("The data corresponding to this ticker is missing")
    relevant_keys = {
      'Current Price' : raw_df.get('currentPrice', 'NaN'),
      'Market Cap' : raw_df.get('marketCap', 'NaN'),
      'Enterprise Value' : raw_df.get('enterpriseValue', 'NaN'),
      'Shares Outstanding' : raw_df.get('sharesOutstanding', 'NaN'),
      'Beta' : raw_df.get('beta','NaN'),
    }
    return relevant_keys