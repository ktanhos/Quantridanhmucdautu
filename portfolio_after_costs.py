from __future__ import annotations
import pandas as pd

def calculate_trading_cost(traded_value,buy=True,fee_rate=0.001,sell_tax_rate=0.001):
    value=float(traded_value or 0);return value*(fee_rate+(0 if buy else sell_tax_rate))

def calculate_custody_cost(share_count,months=1,fee_per_share_month=0.27):
    return float(share_count or 0)*float(months)*float(fee_per_share_month)

def calculate_margin_cost(margin_balance,annual_rate=0.12,days=1):
    return float(margin_balance or 0)*float(annual_rate)*float(days)/365

def calculate_after_cost_returns(gross_returns,turnover=None,fee_rate=0.001,sell_tax_rate=0.001):
    gross=pd.Series(gross_returns,dtype=float)
    if turnover is None:return gross.copy()
    turn=pd.Series(turnover,dtype=float).reindex(gross.index).fillna(0)
    cost_rate=turn*(fee_rate+sell_tax_rate/2)
    return gross-cost_rate

def performance_summary(returns,after_cost_returns,benchmark_returns=None):
    def stats(r):
        r=pd.Series(r,dtype=float).dropna()
        if r.empty:return {'Cumulative Return':0,'Annualized Return':0,'Annualized Volatility':0,'Sharpe Ratio':0,'Maximum Drawdown':0}
        wealth=(1+r).cumprod();years=len(r)/252;ann=wealth.iloc[-1]**(1/years)-1 if years>0 else 0;vol=r.std()*252**0.5;sharpe=ann/vol if vol>0 else 0;dd=wealth/wealth.cummax()-1
        return {'Cumulative Return':wealth.iloc[-1]-1,'Annualized Return':ann,'Annualized Volatility':vol,'Sharpe Ratio':sharpe,'Maximum Drawdown':dd.min()}
    result={'Trước chi phí':stats(returns),'Sau chi phí':stats(after_cost_returns)}
    if benchmark_returns is not None:result['Benchmark']=stats(benchmark_returns)
    return result
