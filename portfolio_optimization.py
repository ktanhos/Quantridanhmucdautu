from __future__ import annotations
import numpy as np
import pandas as pd

def _annual_stats(returns):
    r=returns.apply(pd.to_numeric,errors='coerce').dropna(how='all')
    return r,r.mean()*252,r.cov()*252

def _project_weights(w,max_weight):
    w=np.maximum(np.asarray(w,dtype=float),0.0);n=len(w)
    if n==0:return w
    max_weight=max(float(max_weight),1.0/n)
    if w.sum()<=0:w=np.ones(n)/n
    result=np.zeros(n);active=np.ones(n,dtype=bool);remaining=1.0
    for _ in range(n+1):
        idx=np.where(active)[0]
        if len(idx)==0:break
        base=w[idx];proposal=(base/base.sum()*remaining) if base.sum()>0 else np.ones(len(idx))*remaining/len(idx)
        over=proposal>max_weight+1e-12
        if not over.any():result[idx]=proposal;break
        capped=idx[over];result[capped]=max_weight;active[capped]=False;remaining-=max_weight*len(capped)
    return result/result.sum() if result.sum()>0 else np.ones(n)/n

def _metrics(w,mu,cov,rf=0):
    ret=float(w@mu);vol=float(np.sqrt(max(w@cov@w,0)));sh=(ret-rf)/vol if vol>0 else np.nan
    return ret,vol,sh

def optimize_portfolios(returns,max_weight=0.10,risk_free_rate=0.0,target_return=None):
    r,mu,cov=_annual_stats(returns);n=len(mu);names=list(mu.index)
    if n<2:raise ValueError('Cần ít nhất 2 cổ phiếu để tối ưu hóa danh mục.')
    requested_max_weight=float(max_weight);effective_max_weight=max(requested_max_weight,1.0/n)
    inv=np.linalg.pinv(cov.values+np.eye(n)*1e-8);w_mv=_project_weights(inv@np.ones(n),effective_max_weight)
    w_equal=np.ones(n)/n;w_mr=_project_weights(np.maximum(mu.values,0),effective_max_weight)
    w_max=np.zeros(n);w_max[int(np.nanargmax(mu.values))]=1;w_max=_project_weights(w_max,effective_max_weight)
    rng=np.random.default_rng(42);best=w_mv;best_s=-np.inf
    for _ in range(15000):
        w=_project_weights(rng.dirichlet(np.ones(n)),effective_max_weight);_,_,s=_metrics(w,mu.values,cov.values,risk_free_rate)
        if np.isfinite(s) and s>best_s:best_s=s;best=w
    w_opt=best
    if target_return is not None:
        target=float(target_return);best_target=None;best_vol=np.inf
        for _ in range(20000):
            w=_project_weights(rng.dirichlet(np.ones(n)),effective_max_weight);ret,vol,_=_metrics(w,mu.values,cov.values,risk_free_rate)
            if ret>=target and vol<best_vol:best_target=w;best_vol=vol
        if best_target is not None:w_opt=best_target
    portfolios=[('Phân bổ tham chiếu',w_equal),('Minimum Variance',w_mv),('Optimal Risky',w_opt),('Maximum Return',w_max)]
    rows=[]
    for label,w in portfolios:
        ret,vol,sh=_metrics(w,mu.values,cov.values,risk_free_rate);rows.append({'Danh mục':label,'Lợi suất kỳ vọng':ret,'Độ biến động':vol,'Sharpe Ratio':sh})
    return {'returns':r,'expected_returns':mu,'covariance':cov,'summary':pd.DataFrame(rows).set_index('Danh mục'),'weights':pd.DataFrame({label:w for label,w in portfolios},index=names),'requested_max_weight':requested_max_weight,'effective_max_weight':effective_max_weight,'universe_size':n}
