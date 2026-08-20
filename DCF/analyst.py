from dataCollector import FinancialCollector
from fundamentalRatios import FundamentalRatios
from parametersForDCF import DCFParameters
from DCF import DCF
from DBManager import DataBaseManager
from LLMAnalyst import GROQAnalyst
from datetime import datetime
import os

def analyse(ticker, parameter_for_comp_dcf_parameters, api_key) -> str:
  collector = FinancialCollector(symbol=ticker)
  ratios = FundamentalRatios(collector= collector)
  prof_ratios = ratios.get_profitability_ratios()
  lev_ratios = ratios.get_leverage_ratios()
  op_ratios = ratios.get_operating_ratios()
  val_ratios = ratios.get_valuation_ratios()

  params = DCFParameters(
    collector= collector,
    growth_rate_i= parameter_for_comp_dcf_parameters['growth_rate_i'],
    growth_rate_f= parameter_for_comp_dcf_parameters['growth_rate_f'],
    no_of_years= parameter_for_comp_dcf_parameters['no_of_years'],
    terminal_growth_rate= parameter_for_comp_dcf_parameters['terminal_growth_rate'],
    risk_free_rate= parameter_for_comp_dcf_parameters['risk_free_rate'],
    erp= parameter_for_comp_dcf_parameters['erp'],
    margin_of_safety= parameter_for_comp_dcf_parameters['margin_of_safety']
  )

  dcf = DCF(collector=collector, values= params)
  dcf_result = dcf.get_valuation()
  timestamp = datetime.now().isoformat()

  db = DataBaseManager("financial_data.db")
  db.store_ratios(ticker, 'profitability', prof_ratios, timestamp= timestamp)
  db.store_ratios(ticker, 'leverage',      lev_ratios,timestamp= timestamp)
  db.store_ratios(ticker, 'operating',     op_ratios,timestamp= timestamp)
  db.store_ratios(ticker, 'valuation',     val_ratios,timestamp= timestamp)

  db.store_dcf_summary(ticker, dcf_result)

  stored_ratios = db.get_ratios(ticker)
  stored_dcf    = db.get_dcf_summary(ticker)

  prompt = f"""
  You are an expert Indian equity analyst.
  Analyze {ticker} based on the following financial data:

  PROFITABILITY RATIOS:
  {stored_ratios['PROFITABILITY_RATIOS'].to_string()}

  LEVERAGE RATIOS:
  {stored_ratios['LEVERAGE_RATIOS'].to_string()}

  OPERATING RATIOS:
  {stored_ratios['OPERATING_RATIOS'].to_string()}

  VALUATION RATIOS:
  {stored_ratios['VALUATION_RATIOS'].to_string()}

  DCF SUMMARY:
  {stored_dcf.to_string()}

  Write exactly two paragraphs:
  BULLISH VIEW: (one paragraph making the case for buying)
  BEARISH VIEW: (one paragraph making the case for caution)
  """

  analyst = GROQAnalyst(API_key=api_key)
  analysis = analyst.get_analysis(prompt=prompt)
  return analysis

dcf_params = {
    'growth_rate_i'       : 10,
    'growth_rate_f'       : 7,
    'no_of_years'         : 10,
    'terminal_growth_rate': 5,
    'risk_free_rate'      : 7,
    'erp'                 : 6,
    'margin_of_safety'    : 10
}


api_key = os.getenv("GROQ_API_KEY")
result= analyse("TCS.NS", dcf_params, api_key)
print(result)


