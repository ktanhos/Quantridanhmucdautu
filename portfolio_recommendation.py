from __future__ import annotations
import numpy as np
import pandas as pd


def compare_current_to_target(current_weights,target_weights):
    current=pd.Series(current_weights,dtype=float)
    target=pd.Series(target_weights,dtype=float)
    names=current.index.union(target.index)
    current=current.reindex(names).fillna(0)
    target=target.reindex(names).fillna(0)
    current=current/current.sum() if current.sum()!=0 else current
    target=target/target.sum() if target.sum()!=0 else target
    out=pd.DataFrame({'Tỷ trọng hiện tại':current,'Tỷ trọng mục tiêu':target})
    out['Thay đổi tỷ trọng']=out['Tỷ trọng mục tiêu']-out['Tỷ trọng hiện tại']
    return out.sort_values('Thay đổi tỷ trọng',ascending=False)


def regime_adjustment(weights,regime,equity_min,equity_max):
    w=pd.Series(weights,dtype=float).clip(lower=0)
    if w.sum()==0:return w
    equity_target=(float(equity_min)+float(equity_max))/2
    return w/w.sum()*equity_target


def risk_aversion_from_profile(risk_tolerance):
    score=float(risk_tolerance)
    return float(np.clip(6.0-4.0*score/100.0,2.0,6.0))


def build_complete_portfolio(orp_weights,expected_returns,covariance,risk_free_rate,risk_tolerance,
                             allow_leverage=False,margin_rate=0.12,max_leverage=1.50,
                             current_weights=None):
    """Chuyển Optimal Risky Portfolio thành Complete Portfolio.

    Không vay: y nằm trong 0 đến 1.
    Có vay Margin: nếu nghiệm y lớn hơn 1, phần y trừ 1 là vốn vay.
    Khi vay, phần vốn vượt 100 phần trăm chịu chi phí margin_rate.
    """
    w_orp=pd.Series(orp_weights,dtype=float).clip(lower=0)
    if w_orp.sum()<=0: raise ValueError('Optimal Risky Portfolio không có tỷ trọng hợp lệ.')
    w_orp=w_orp/w_orp.sum()
    mu=pd.Series(expected_returns,dtype=float).reindex(w_orp.index).fillna(0)
    cov=pd.DataFrame(covariance,dtype=float).reindex(index=w_orp.index,columns=w_orp.index).fillna(0)
    rf=float(risk_free_rate)
    margin=float(margin_rate)
    A=risk_aversion_from_profile(risk_tolerance)
    er_orp=float(w_orp.dot(mu))
    variance_orp=float(w_orp.dot(cov).dot(w_orp))
    sigma_orp=float(np.sqrt(max(variance_orp,0.0)))
    excess=er_orp-rf
    y_no_borrow=float(excess/(A*variance_orp)) if variance_orp>1e-12 else 0.0
    y_no_borrow=float(np.clip(y_no_borrow,0.0,1.0))
    if allow_leverage and margin>rf and variance_orp>1e-12:
        y_with_margin=float((er_orp-margin)/(A*variance_orp))
    else:
        y_with_margin=y_no_borrow
    y=float(np.clip(max(y_no_borrow,y_with_margin) if allow_leverage else y_no_borrow,0.0,float(max_leverage if allow_leverage else 1.0)))
    complete_equity=w_orp*y
    borrowed=max(0.0,y-1.0)
    defensive=max(0.0,1.0-y)
    borrowing_cost=borrowed*margin
    complete_return=rf+y*excess-borrowing_cost
    complete_vol=abs(y)*sigma_orp
    complete_sharpe=(complete_return-rf)/complete_vol if complete_vol>1e-12 else np.nan
    comparison=compare_current_to_target(current_weights if current_weights is not None else pd.Series(dtype=float),complete_equity)
    return {
        'orp_weights':w_orp,'complete_equity_weights':complete_equity,'defensive_weight':defensive,
        'borrowed_weight':borrowed,'expected_return_orp':er_orp,'volatility_orp':sigma_orp,
        'variance_orp':variance_orp,'risk_free_rate':rf,'margin_rate':margin,'risk_aversion':A,
        'excess_return':excess,'y_raw_no_borrow':y_no_borrow,'y_raw_with_margin':y_with_margin,'y':y,
        'complete_expected_return':complete_return,'complete_volatility':complete_vol,
        'complete_sharpe':complete_sharpe,'borrowing_cost':borrowing_cost,
        'allow_leverage':bool(allow_leverage),'max_leverage':float(max_leverage),'comparison':comparison,
    }


def build_recommendation(current_weights,target_weights,regime,equity_min,equity_max,max_single_stock_weight=1.0,complete_portfolio=None):
    target=pd.Series(target_weights,dtype=float).clip(lower=0)
    if target.sum()==0: raise ValueError('Danh mục mục tiêu không có tỷ trọng hợp lệ.')
    target=target/target.sum()
    max_single=float(max_single_stock_weight)
    if complete_portfolio is not None:
        adjusted=pd.Series(complete_portfolio['complete_equity_weights'],dtype=float)
        defensive=float(complete_portfolio['defensive_weight'])
        borrowed=float(complete_portfolio['borrowed_weight'])
    else:
        if target.max()>max_single+1e-8: raise ValueError(f'Phương án mục tiêu có tỷ trọng {target.max():.2%}, vượt giới hạn {max_single:.2%} cho một cổ phiếu.')
        adjusted=regime_adjustment(target,regime,equity_min,equity_max)
        defensive=max(0.,1-adjusted.sum())
        borrowed=0.0
    if adjusted.max()>max_single+1e-8:
        raise ValueError(f'Complete Portfolio có tỷ trọng cổ phiếu {adjusted.max():.2%}, vượt giới hạn {max_single:.2%}.')
    return {'target_equity_weights':adjusted,'defensive_weight':defensive,'borrowed_weight':borrowed,
            'comparison':compare_current_to_target(current_weights,adjusted),'regime':regime,
            'complete_portfolio':complete_portfolio}
