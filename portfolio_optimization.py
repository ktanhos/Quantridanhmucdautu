from __future__ import annotations
import numpy as np
import pandas as pd


def _annual_stats(returns):
    r=returns.apply(pd.to_numeric,errors='coerce').dropna(how='all')
    return r,r.mean()*252,r.cov()*252


def _project_weights(w,max_weight):
    w=np.maximum(np.asarray(w,dtype=float),0.0)
    n=len(w)
    if n==0:return w
    max_weight=float(max_weight)
    if max_weight<=0 or n*max_weight<1-1e-10:
        raise ValueError('Ràng buộc tỷ trọng không khả thi: tổng giới hạn của các mã nhỏ hơn 100%.')
    if w.sum()<=0:w=np.ones(n)/n
    w=w/w.sum()
    result=np.zeros(n)
    active=np.ones(n,dtype=bool)
    remaining=1.0
    for _ in range(n+1):
        idx=np.where(active)[0]
        if len(idx)==0:break
        base=w[idx]
        proposal=base/base.sum()*remaining if base.sum()>0 else np.ones(len(idx))*remaining/len(idx)
        over=proposal>max_weight+1e-12
        if not over.any():
            result[idx]=proposal
            remaining=0.0
            break
        capped=idx[over]
        result[capped]=max_weight
        active[capped]=False
        remaining-=max_weight*len(capped)
        if remaining < -1e-9:
            raise ValueError('Không thể phân bổ đủ 100% với giới hạn hiện tại.')
    if remaining>1e-8:
        idx=np.where(active)[0]
        if len(idx)==0:raise ValueError('Không thể phân bổ đủ 100% với giới hạn hiện tại.')
        result[idx]+=remaining/len(idx)
    return result/result.sum()


def _metrics(w,mu,cov,rf=0):
    ret=float(w@mu)
    vol=float(np.sqrt(max(w@cov@w,0)))
    sh=(ret-rf)/vol if vol>0 else np.nan
    return ret,vol,sh


def optimize_portfolios(returns,max_weight=0.10,risk_free_rate=0.0,target_return=None):
    r,mu,cov=_annual_stats(returns)
    n=len(mu)
    names=list(mu.index)
    if n<2:raise ValueError('Cần ít nhất 2 cổ phiếu để tối ưu hóa danh mục.')

    requested_max_weight=float(max_weight)
    required_assets=int(np.ceil(1/requested_max_weight)) if requested_max_weight>0 else n
    constraint_feasible=(n*requested_max_weight)>=1-1e-10

    # Khi ràng buộc không khả thi, không tự ý nâng giới hạn.
    # Các nghiệm bên dưới chỉ là nghiệm tham khảo để cho người dùng thấy mô hình đang nghiêng về đâu.
    effective_max_weight=requested_max_weight if constraint_feasible else 1.0

    inv=np.linalg.pinv(cov.values+np.eye(n)*1e-8)
    raw_mv=inv@np.ones(n)
    if constraint_feasible:
        w_mv=_project_weights(raw_mv,effective_max_weight)
    else:
        w_mv=np.maximum(raw_mv,0.0)
        w_mv=w_mv/w_mv.sum() if w_mv.sum()>0 else np.ones(n)/n

    w_equal=np.ones(n)/n

    positive_mu=np.maximum(mu.values,0)
    raw_mr=positive_mu if positive_mu.sum()>0 else np.ones(n)
    if constraint_feasible:
        w_mr=_project_weights(raw_mr,effective_max_weight)
    else:
        w_mr=raw_mr/raw_mr.sum()

    w_max=np.zeros(n)
    w_max[int(np.nanargmax(mu.values))]=1.0
    if constraint_feasible:
        w_max=_project_weights(w_max,effective_max_weight)

    rng=np.random.default_rng(42)
    best=w_mv
    best_s=-np.inf
    for _ in range(20000):
        raw=rng.dirichlet(np.ones(n))
        w=_project_weights(raw,effective_max_weight) if constraint_feasible else raw
        _,_,s=_metrics(w,mu.values,cov.values,risk_free_rate)
        if np.isfinite(s) and s>best_s:
            best_s=s
            best=w
    w_opt=best

    target_feasible=False
    if target_return is not None:
        target=float(target_return)
        best_target=None
        best_vol=np.inf
        for _ in range(30000):
            raw=rng.dirichlet(np.ones(n))
            w=_project_weights(raw,effective_max_weight) if constraint_feasible else raw
            ret,vol,_=_metrics(w,mu.values,cov.values,risk_free_rate)
            if ret>=target and vol<best_vol:
                best_target=w
                best_vol=vol
        if best_target is not None:
            w_opt=best_target
            target_feasible=True

    portfolios=[
        ('Phân bổ tham chiếu',w_equal),
        ('Minimum Variance',w_mv),
        ('Optimal Risky',w_opt),
        ('Maximum Return',w_max),
    ]
    rows=[]
    for label,w in portfolios:
        ret,vol,sh=_metrics(w,mu.values,cov.values,risk_free_rate)
        rows.append({'Danh mục':label,'Lợi suất kỳ vọng':ret,'Độ biến động':vol,'Sharpe Ratio':sh})

    return {
        'returns':r,
        'expected_returns':mu,
        'covariance':cov,
        'summary':pd.DataFrame(rows).set_index('Danh mục'),
        'weights':pd.DataFrame({label:w for label,w in portfolios},index=names),
        'requested_max_weight':requested_max_weight,
        'effective_max_weight':effective_max_weight,
        'universe_size':n,
        'constraint_feasible':constraint_feasible,
        'required_assets':required_assets,
        'target_feasible':target_feasible,
    }
