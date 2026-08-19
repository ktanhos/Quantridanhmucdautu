from __future__ import annotations
import numpy as np
import pandas as pd

def _clean_returns(returns):
    out=returns.apply(pd.to_numeric,errors='coerce')
    return out.replace([np.inf,-np.inf],np.nan).dropna(how='all')

def portfolio_returns(returns,weights):
    r=_clean_returns(returns);w=pd.Series(weights,dtype=float).reindex(r.columns).fillna(0.)
    if w.abs().sum()==0:raise ValueError('Danh mục chưa có tỷ trọng hợp lệ.')
    w=w/w.sum();return r.mul(w,axis=1).sum(axis=1,min_count=1).dropna()

def max_drawdown(series):
    wealth=(1+series).cumprod();return float((wealth/wealth.cummax()-1).min())

def calculate_portfolio_risk(returns,weights,benchmark_returns=None,risk_free_rate=0.):
    r=_clean_returns(returns);w=pd.Series(weights,dtype=float).reindex(r.columns).fillna(0.)
    if w.sum()==0:raise ValueError('Tổng tỷ trọng danh mục bằng 0.')
    w=w/w.sum();pr=portfolio_returns(r,w)
    annual_return=float((1+pr).prod()**(252/len(pr))-1);annual_vol=float(pr.std(ddof=1)*np.sqrt(252));sharpe=(annual_return-risk_free_rate)/annual_vol if annual_vol>0 else np.nan;mdd=max_drawdown(pr)
    var95=float(pr.quantile(.05));cvar95=float(pr[pr<=var95].mean()) if (pr<=var95).any() else var95
    beta=tracking_error=information_ratio=np.nan
    if benchmark_returns is not None:
        b=pd.to_numeric(benchmark_returns,errors='coerce').rename('benchmark');j=pd.concat([pr.rename('portfolio'),b],axis=1).dropna()
        if len(j)>=20 and j['benchmark'].var(ddof=1)>0:
            beta=float(j['portfolio'].cov(j['benchmark'])/j['benchmark'].var(ddof=1));active=j['portfolio']-j['benchmark'];tracking_error=float(active.std(ddof=1)*np.sqrt(252));pa=(1+j['portfolio']).prod()**(252/len(j))-1;ba=(1+j['benchmark']).prod()**(252/len(j))-1;information_ratio=float((pa-ba)/tracking_error) if tracking_error>0 else np.nan
    covariance=r.cov()*252;marginal=covariance.dot(w);variance=float(w.dot(covariance).dot(w));risk_contribution=w*marginal/variance if variance>0 else pd.Series(np.nan,index=w.index)
    return {'portfolio_returns':pr,'weights':w,'annual_return':annual_return,'annual_volatility':annual_vol,'sharpe':sharpe,'max_drawdown':mdd,'var_95_daily':var95,'cvar_95_daily':cvar95,'beta':beta,'tracking_error':tracking_error,'information_ratio':information_ratio,'risk_contribution':risk_contribution,'correlation':r.corr(),'concentration_hhi':float((w[w!=0]**2).sum())}
