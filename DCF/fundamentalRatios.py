import numpy as np
import pandas as pd
from dataCollector import FinancialCollector

class FundamentalRatios:

  def __init__(self, collector: FinancialCollector):
    self.collector = collector
    self.pl = self.collector.get_p_and_l()
    self.bs = self.collector.get_balance_sheet()
    self.cf = self.collector.get_cash_flow()
    self.info = self.collector.get_info()
    self.years = self.pl.index[:3]

  # column[year] == self.bs.loc[year, 'Total Assets']
  def _avg(self, year, column):
    return (column[year] + column[year-1]) / 2


  
  def get_profitability_ratios(self) -> pd.DataFrame:
    results = {}
    for each_year in self.years:
      self.calculated_ebita = (
        self.pl['Total Revenue'][each_year] - 
        self.pl['Other Non Operating Income Expenses'][each_year]
        ) - (
          self.pl['Total Expenses'][each_year] - self.pl['Interest Expense'][each_year]
            - self.pl['Depreciation And Amortization In Income Statement'][each_year]
        )
      mentioned_ebita = self.pl['EBITDA'][each_year]
      ebita_margin = self.calculated_ebita/(self.pl['Total Revenue'][each_year] - self.pl['Other Non Operating Income Expenses'][each_year])
      pat_margin = self.pl['Net Income'][each_year]/self.pl['Total Revenue'][each_year]
      return_on_equity = self.pl['Net Income'][each_year]/self.bs['Stockholders Equity'][each_year]
      K1 = self.pl['Net Income'][each_year] / self.pl['Total Revenue'][each_year]
      K2 = self.pl['Total Revenue'][each_year] / self._avg(each_year, self.bs['Total Assets'])
      K3 = self._avg(each_year, self.bs['Total Assets']) / self.bs['Stockholders Equity'][each_year]
      return_on_equity_Dupoint = K1*K2*K3
      return_on_assets = (self.pl['Net Income'][each_year] + self.pl['Interest Expense'][each_year]*(1-self.pl['Tax Rate For Calcs'][each_year])) / self._avg(each_year, self.bs['Total Assets'])
      invested_capital = (self.bs['Current Debt And Capital Lease Obligation'][each_year]
      +self.bs['Long Term Debt And Capital Lease Obligation'][each_year]
      +self.bs['Stockholders Equity'][each_year])
      return_on_cap_employed = self.pl['EBIT'][each_year] / invested_capital

      
      
      results[each_year] = {
        "Calculated EBITA" : self.calculated_ebita,
        "Mentioned EBITA" : mentioned_ebita,
        "EBITA MArgin" : ebita_margin,
        "PAT Margin" : pat_margin,
        "ROE" : return_on_equity,
        "ROE DuPoint" : return_on_equity_Dupoint,
        "ROA" : return_on_assets,
        "ROCE" : return_on_cap_employed,
      }

    return pd.DataFrame(results).T


  
  def get_leverage_ratios(self) -> pd.DataFrame:
    results = {}
    for each_year in self.years:
      interest_coverage_ratio = self.pl['EBIT'][each_year] / self.pl['Interest Expense'][each_year]
      debt_to_equity_ratio = self.bs['Total Debt'][each_year] / self.bs['Stockholders Equity'][each_year]
      total_debt = self.bs['Total Debt'][each_year]
      average_total_assets = self._avg(each_year, self.bs['Total Assets'])
      financial_leverage_ratio = average_total_assets / self.bs['Stockholders Equity'][each_year]

      results[each_year] = {
        "Interest Coverage Ratio" : interest_coverage_ratio,
        "Debt to Equity" : debt_to_equity_ratio,
        "Total Debt" : total_debt,
        "Financial Leverage Ratio" : financial_leverage_ratio,
      }

    return pd.DataFrame(results).T

  def get_operating_ratios(self) -> pd.DataFrame:
    results = {}
    for each_year in self.years:
      fixed_asset_turnover = self.pl['Operating Revenue'][each_year] / self._avg(each_year, self.bs['Net PPE'])
      total_asset_turnover = self.pl['Operating Revenue'][each_year] / self._avg(each_year,self.bs['Total Assets'])
      working_capital = self.bs['Current Assets'][each_year] - self.bs['Current Liabilities'][each_year]
      working_capital_turnover = self.pl['Total Revenue'][each_year] / working_capital
      inventory_turnover = self.pl['Cost Of Revenue'][each_year] / self._avg(each_year, self.bs['Inventory'])
      accounts_receivable_turnover = self.pl['Total Revenue'][each_year] / self._avg(each_year,self.bs['Accounts Receivable'])
      days_sales_outstanding = 365 / accounts_receivable_turnover

      results[each_year] = {
        "Fixed Asset Turnover" : fixed_asset_turnover,
        "Total Asset Turnover" : total_asset_turnover,
        "Working Capital" : working_capital,
        "Working Capital Turnover" : working_capital_turnover,
        "Inventory Turnover" : inventory_turnover,
        "Accounts Receivable Turnover" : accounts_receivable_turnover,
        "Days Sales Outstanding" : days_sales_outstanding,
      } 

    return pd.DataFrame(results).T

  def get_valuation_ratios(self) -> pd.DataFrame:
    results = {}
    for each_year in self.years:
      sales_per_share = self.pl['Total Revenue'][each_year] / self.bs['Ordinary Shares Number'][each_year]
      book_value = self.bs['Stockholders Equity'][each_year] / self.bs['Ordinary Shares Number'][each_year]
      earing_per_share = self.pl['Net Income Common Stockholders'][each_year] / self.pl['Basic Average Shares'][each_year]
      current_share_price = self.info['Current Price']
      price_to_book = current_share_price / book_value
      price_to_sales = current_share_price / earing_per_share
      price_to_earning_ratio = current_share_price / self.pl['Basic Average Shares'][each_year]

      results[each_year] = {
        "Sales per Share" : sales_per_share,
        "Book Value" : book_value,
        "Earning per Share" : earing_per_share,
        "Current share price" : current_share_price,
        "P/B" : price_to_book,
        "P/S" : price_to_sales,
        "P/E" : price_to_earning_ratio,

      }


    return pd.DataFrame(results).T
