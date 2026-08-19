from __future__ import annotations
import numpy as np
import pandas as pd

def _annual_stats(returns):
    r=returns.apply(pd.to_numeric,errors='coerce').dropna(how='all')
    return r,r.mean()*252,r.cov()*252

def _project_weights(w,max_weight):
    w=np.clip(np.asarray(w,dtype=float),0,max_weight)
    if w.sum()<=0:w=np.ones(len(w))/len(w)
    for _ in range(100):
        excess=w.sum()-1
        if abs(excess)<1e-10:break
        if excess>0:
            free=w<max_weight-1e-10
            if not free.any():break
            w[free]+=excess/free.sum();w=np.minimum(w,max_weight)
        else:
            free=w>1e-10
            if not free.any():break
            w[free]+=(-excess)/free.sum();w=np.maximum(w,0)
    return w/w.sum()

def _metrics(w,mu,cov,rf=0):
    ret=float(w@mu);vol=float(np.sqrt(max(w@cov@w,0)));sh=(ret-rf)/vol if vol>0 else np.nan
    return ret,vol,sh

def optimize_portfolios(returns,max_weight=0.10,risk_free_rate=0.0,target_return=None):
    r,mu,cov=_annual_stats(returns);n=len(mu);names=list(mu.index)
    if n<2:raise ValueError('Cần ít nhất 2 cổ phiếu để tối ưu hóa danh mục.')
    inv=np.linalg.pinv(cov.values+np.eye(n)*1e-8);w_mv=_project_weights(inv@np.ones(n),max_weight)
    w_mr=_project_weights(np.maximum(mu.values,0),max_weight)
    w_max=np.zeros(n);w_max[int(np.nanargmax(mu.values))]=1;w_max=_project_weights(w_max,max_weight)
    rng=np.random.default_rng(42);best=w_mv;best_s=-np.inf
    for _ in range(15000):
        w=_project_weights(rng.dirichlet(np.ones(n)),max_weight);_,_,s=_metrics(w,mu.values,cov.values,risk_free_rate)
        if np.isfinite(s) and s>best_s:best_s=s;best=w
    w_opt=best
    if target_return is not None:
        target=float(target_return);best_target=None;best_vol=np.inf
        for _ in range(20000):
            w=_project_weights(rng.dirichlet(np.ones(n)),max_weight);ret,vol,_=_metrics(w,mu.values,cov.values,risk_free_rate)
            if ret>=target and vol<best_vol:best_target=w;best_vol=vol
        if best_target is not None:w_opt=best_target
    rows=[]
    for label,w in [('Minimum Variance',w_mv),('Optimal Risky',w_opt),('Maximum Return',w_max)]:
        ret,vol,sh=_metrics(w,mu.values,cov.values,risk_free_rate);rows.append({'Danh mục':label,'Lợi suất kỳ vọng':ret,'Độ biến động':vol,'Sharpe Ratio':sh})
    return {'returns':r,'expected_returns':mu,'covariance':cov,'summary':pd.DataFrame(rows).set_index('Danh mục'),'weights':pd.DataFrame({'Minimum Variance':w_mv,'Optimal Risky':w_opt,'Maximum Return':w_max},index=names)}
