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


def build_recommendation(current_weights,target_weights,regime,equity_min,equity_max,max_single_stock_weight=1.0):
    target=pd.Series(target_weights,dtype=float).clip(lower=0)
    if target.sum()==0:
        raise ValueError('Danh mục mục tiêu không có tỷ trọng hợp lệ.')
    target=target/target.sum()
    max_single=float(max_single_stock_weight)
    if target.max()>max_single+1e-8:
        raise ValueError(f'Phương án mục tiêu có tỷ trọng {target.max():.2%}, vượt giới hạn {max_single:.2%} cho một cổ phiếu.')
    adjusted=regime_adjustment(target,regime,equity_min,equity_max)
    defensive=max(0.,1-adjusted.sum())
    if adjusted.max()>max_single+1e-8:
        raise ValueError('Tỷ trọng sau điều chỉnh Market Regime vượt giới hạn một cổ phiếu.')
    return {
        'target_equity_weights':adjusted,
        'defensive_weight':defensive,
        'comparison':compare_current_to_target(current_weights,adjusted),
        'regime':regime,
    }


def risk_aversion_from_profile(risk_tolerance):
    """Quy đổi lựa chọn phổ thông thành hệ số ngại rủi ro nội bộ.

    Đây là tham số hướng dẫn của ứng dụng, không phải thang điểm do CFA quy định.
    Điểm càng cao nghĩa là càng chấp nhận rủi ro và hệ số A càng thấp.
    """
    score=float(risk_tolerance)
    return float(np.clip(6.0-4.0*score/100.0,2.0,6.0))


def build_complete_portfolio(orp_weights, expected_returns, covariance, risk_free_rate,
                             risk_tolerance, regime='Trung tính', equity_min=0.0,
                             equity_max=1.0, max_single_stock_weight=1.0,
                             current_weights=None):
    """Chuyển Optimal Risky Portfolio thành Complete Portfolio theo utility.

    y* = (E[R_ORP] - Rf) / (A * sigma_ORP^2)

    Phiên bản hiện tại không cho phép bán khống hoặc đòn bẩy, nên y nằm trong 0 đến 1.
    Market Regime được dùng như giới hạn trên của mức phơi nhiễm cổ phiếu.
    """
    w_orp=pd.Series(orp_weights,dtype=float).clip(lower=0)
    if w_orp.sum()<=0:
        raise ValueError('Optimal Risky Portfolio không có tỷ trọng hợp lệ.')
    w_orp=w_orp/w_orp.sum()
    mu=pd.Series(expected_returns,dtype=float).reindex(w_orp.index).fillna(0)
    cov=pd.DataFrame(covariance,dtype=float).reindex(index=w_orp.index,columns=w_orp.index).fillna(0)
    rf=float(risk_free_rate)
    A=risk_aversion_from_profile(risk_tolerance)
    er_orp=float(w_orp.dot(mu))
    variance_orp=float(w_orp.dot(cov).dot(w_orp))
    sigma_orp=float(np.sqrt(max(variance_orp,0.0)))
    excess=er_orp-rf
    y_raw=float(excess/(A*variance_orp)) if variance_orp>1e-12 else 0.0
    equity_cap=min(1.0,float(equity_max))
    y=float(np.clip(y_raw,0.0,equity_cap))
    complete_equity=w_orp*y
    defensive=max(0.0,1.0-y)
    if complete_equity.max()>float(max_single_stock_weight)+1e-8:
        raise ValueError('Complete Portfolio vượt giới hạn tỷ trọng một cổ phiếu.')
    complete_return=rf+y*excess
    complete_vol=abs(y)*sigma_orp
    complete_sharpe=(complete_return-rf)/complete_vol if complete_vol>1e-12 else np.nan
    comparison=compare_current_to_target(current_weights if current_weights is not None else pd.Series(dtype=float),complete_equity)
    return {
        'orp_weights':w_orp,
        'complete_equity_weights':complete_equity,
        'defensive_weight':defensive,
        'expected_return_orp':er_orp,
        'volatility_orp':sigma_orp,
        'variance_orp':variance_orp,
        'risk_free_rate':rf,
        'risk_aversion':A,
        'excess_return':excess,
        'y_raw':y_raw,
        'y':y,
        'complete_expected_return':complete_return,
        'complete_volatility':complete_vol,
        'complete_sharpe':complete_sharpe,
        'regime':regime,
        'equity_cap':equity_cap,
        'equity_min_regime':float(equity_min),
        'equity_max_regime':float(equity_max),
        'comparison':comparison,
    }
