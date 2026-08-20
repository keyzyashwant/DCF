import pandas as pd
import math
from dataCollector import FinancialCollector
from parametersForDCF import DCFParameters


class DCF:
  def __init__(self, collector: FinancialCollector, values: DCFParameters):
    self.collector = collector
    self.values = values

    self.pl = self.collector.get_p_and_l()
    self.bs = self.collector.get_balance_sheet()
    self.cf = self.collector.get_cash_flow()
    self.info = self.collector.get_info()

    self.params = self.values.get_parameters()

    self.initial_growth_rate = self.params['user_inputs']['InitialGrowthRate']
    self.final_growth_rate = self.params['user_inputs']['FinalGrowthRate']
    self.no_of_years = self.params['user_inputs']['NoOfYears']
    self.terminal_rate    = self.params['user_inputs']['TerminalGrowthRate']
    self.wacc             = self.params['computed_values']['WACC']
    self.margin_of_safety = self.params['user_inputs']['MarginOfSafety']

    self.phase1_years = self.no_of_years//2
    self.phase2_years = self.no_of_years - self.phase1_years
    
    self.share_outStanding = self.info['Shares Outstanding']
    self.year0 = self.cf.index[0]
    self.year1 = self.cf.index[1]


  def _calculate_base_fcf(self,use_reported=False) -> float:
    if use_reported is True:
      fcf_y0 = self.cf['Free Cash Flow'][self.year0]
      fcf_y1 = self.cf['Free Cash Flow'][self.year1]
    # abs() on Capital Expenditure — yfinance stores it as a negative number. 
    else:
      fcf_y0 = self.cf['Operating Cash Flow'][self.year0] - abs(self.cf['Capital Expenditure'][self.year0])
      fcf_y1 = self.cf['Operating Cash Flow'][self.year1] - abs(self.cf['Capital Expenditure'][self.year1])
    return (fcf_y0 + fcf_y1 ) / 2

  def _project_fcf(self,base_fcf) -> list:
    projected = []
    current = base_fcf
    for n in range(self.no_of_years):
      if n < self.phase1_years:
        current = current*(1 + self.initial_growth_rate)
      else:
        current = current*(1 + self.final_growth_rate)
      projected.append(current)
    return projected


  def _discount_fcf(self,projected_fcf) -> list:
    discounted_fcf = []
    discount_factors = []
    for i,fcf in enumerate(projected_fcf):
      year = i + 1
      denominator = (1 + self.wacc) ** year
      discounting_factor = 1 / denominator
      discount_factors.append(discounting_factor)
      present_value = fcf * discounting_factor
      discounted_fcf.append(present_value)
    return discount_factors, discounted_fcf


  def _terminal_value(self,last_projected_fcf) -> float:
    terminal_fcf = last_projected_fcf * (1 + self.terminal_rate)
    terminal_value = terminal_fcf / (self.wacc - self.terminal_rate)
    present_value_of_tv = terminal_value / (1 + self.wacc) ** self.no_of_years
    return present_value_of_tv

  def get_valuation(self) -> pd.DataFrame:
    # DCF from Calculated FCF 
    base_calc = self._calculate_base_fcf(use_reported=False)
    projected_calc = self._project_fcf(base_calc)
    factors, pv_calc = self._discount_fcf(projected_calc)
    pv_tv_calc = self._terminal_value(projected_calc[-1])
    npv_calc = sum(pv_calc) + pv_tv_calc
    intrinsic_calc = npv_calc / self.share_outStanding
    lower_band_value_calc = intrinsic_calc * (1 - self.margin_of_safety)
    upper_band_value_calc = intrinsic_calc * (1 + self.margin_of_safety)

    #DCF from Reported FCF
    base_rep = self._calculate_base_fcf(use_reported=True)
    projected_rep = self._project_fcf(base_rep)
    _, pv_rep = self._discount_fcf(projected_rep)
    pv_tv_rep = self._terminal_value(projected_rep[-1])
    npv_rep = sum(pv_rep) + pv_tv_rep
    intrinsic_rep = npv_rep / self.share_outStanding
    lower_band_value_rep = intrinsic_rep * (1 - self.margin_of_safety)
    upper_band_value_rep = intrinsic_rep * (1 + self.margin_of_safety)

    table = pd.DataFrame({
    'Year'                      : list(range(1, self.no_of_years + 1)),
    'Projected FCF (Calculated)': projected_calc,
    'Discount Factor'           : factors,
    'PV (Calculated)'           : pv_calc,
    'Projected FCF (Reported)'  : projected_rep,
    'PV (Reported)'             : pv_rep,})
    table = table.set_index('Year')

    summary = pd.DataFrame({
    'Projected FCF (Calculated)': [None, None, None, None, None, None],
    'Discount Factor'           : [None, None, None, None, None, None],
    'PV (Calculated)'           : [pv_tv_calc, npv_calc, intrinsic_calc, lower_band_value_calc, upper_band_value_calc, None],
    'Projected FCF (Reported)'  : [None, None, None, None, None, None],
    'PV (Reported)'             : [pv_tv_rep, npv_rep, intrinsic_rep, lower_band_value_rep, upper_band_value_rep, None],
    }, index=[
        'Terminal Value',
        'NPV',
        'Intrinsic Price',
        'Lower Band',
        'Upper Band',
        '---'
    ])

    result = pd.concat([table, summary])
    return result

