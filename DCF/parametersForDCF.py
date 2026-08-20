import pandas as pd
from dataCollector import FinancialCollector

class NumberOfYearsLow(Exception):
  pass

class ImproperRate(Exception):
  pass

class DCFParameters:
  def __init__(self,collector: FinancialCollector, growth_rate_i: float, growth_rate_f:float, no_of_years : int, terminal_growth_rate, risk_free_rate, erp, margin_of_safety):
    if no_of_years <= 5:
      raise NumberOfYearsLow("The no. years are too low!")

    if terminal_growth_rate>= 15:
      raise ImproperRate("Terminal rate too high check again!")
    if terminal_growth_rate<0:
      raise ImproperRate("Terminal rate too low check again!")

    if risk_free_rate>= 15:
      raise ImproperRate("Risk free rate too high!")
    if risk_free_rate<0:
      raise ImproperRate("Risk free rate too low!")
    
    if growth_rate_i>= 15:
      raise ImproperRate("Growth rate too high!")
    if growth_rate_i<=0:
      raise ImproperRate("Growth rate too low!")
    
    if growth_rate_f>= 15:
      raise ImproperRate("Growth rate too high!")
    if growth_rate_f<=0:
      raise ImproperRate("Growth rate too low!")

    if erp>=15:
      raise ImproperRate("ERP too high!")
    if erp<0:
      raise ImproperRate("ERP too low!")

    if margin_of_safety>=12:
      raise ImproperRate("Too Causious!")
    if margin_of_safety<=5:
      raise ImproperRate("Too Risky!")
    
    self.collector = collector
    self.growth_rate_i = growth_rate_i/100
    self.growth_rate_f = growth_rate_f/100
    self.no_of_years = no_of_years
    self.terminal_growth_rate = terminal_growth_rate/100
    self.risk_free_rate = risk_free_rate/100
    self.erp = erp/100
    self.margin_of_safety = margin_of_safety/100

    self.pl = self.collector.get_p_and_l()
    self.bs = self.collector.get_balance_sheet()
    self.cf = self.collector.get_cash_flow()
    self.info = self.collector.get_info()
    self.wacc = self._calculate_wacc()

    if self.terminal_growth_rate >= self.wacc:
      raise ImproperRate("Terminal rate is greater than discount rate(wacc)!")


  def _calculate_wacc(self) -> float:
    #years
    self.year = self.pl.index[0]
    #cost of equity
    self.beta = self.info['Beta']
    self.ke = self.risk_free_rate + (self.beta* self.erp)
    #Cost of Debt
    interest_expense = self.pl['Interest Expense'][self.year]
    total_debt = self.bs['Total Debt'][self.year]

    tax_rate = self.pl['Tax Provision'][self.year] / self.pl['Pretax Income'][self.year]
    self.kd = (interest_expense / total_debt) * (1 - tax_rate)

    equity = self.bs['Stockholders Equity'][self.year]
    debt = self.bs['Total Debt'][self.year]
    total_capital = equity + debt
    we = equity / total_capital
    wd = debt / total_capital

    wacc = (we * self.ke) + (wd * self.kd)
    return wacc



  def get_parameters(self) -> dict:
    results = {
      "user_inputs" : {
        "InitialGrowthRate" : self.growth_rate_i,
        "FinalGrowthRate" : self.growth_rate_f,
        "NoOfYears" : self.no_of_years,
        "TerminalGrowthRate" : self.terminal_growth_rate,
        "RiskFreeRate" : self.risk_free_rate,
        "ERP" : self.erp,
        "MarginOfSafety" : self.margin_of_safety, 
      },
      "computed_values" : {
        "WACC" : self.wacc,
        "CostOfEquity" : self.ke,
        "CostOfDebt" : self.kd,
      }
    }

    return results