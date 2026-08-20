from __future__ import annotations
import numpy as np
import pandas as pd


def compare_current_to_target(current_weights,target_weights):
    current=pd.Series(current_weights,dtype=float);target=pd.Series(target_weights,dtype=float);names=current.index.union(target.index)
    current=current.reindex(names).fillna(0);target=target.reindex(names).fillna(0)
    current=current/current.sum() if current.sum()!=0 else current;target=target/target.sum() if target.sum()!=0 else target
    out=pd.DataFrame({'Tỷ trọng hiện tại':current,'Tỷ trọng mục tiêu':target});out['Thay đổi tỷ trọng']=out['Tỷ trọng mục tiêu']-out['Tỷ trọng hiện tại']
    return out.sort_values('Thay đổi tỷ trọng',ascending=False)


def equity_frame_from_profile(policy):
    score=float(policy.get('risk_capacity',policy.get('risk_tolerance',50)))
    goal=str(policy.get('investor_goal','Tăng trưởng ổn định'))
    if score<=30: low,high=0.20,0.45
    elif score<=60: low,high=0.35,0.70
    else: low,high=0.55,0.90
    if goal=='Bảo toàn vốn': high=min(high,0.55)
    elif goal=='Tăng trưởng cao': low=max(low,0.50);high=min(1.0,max(high,0.90))
    reserve=float(policy.get('emergency_cash_percent',0.0))
    high=max(low,min(high,1.0-reserve))
    return float(low),float(high)


def combine_equity_budgets(profile_min,profile_max,regime_min,regime_max):
    low=max(float(profile_min),float(regime_min))
    high=min(float(profile_max),float(regime_max))
    if low<=high:return low,high,'Giao'
    anchor=(float(regime_min)+float(regime_max))/2
    target=float(np.clip(anchor,float(profile_min),float(profile_max)))
    return target,target,'Điều chỉnh theo giới hạn nhà đầu tư'


def risk_aversion_from_profile(risk_tolerance):
    score=float(risk_tolerance)
    return float(np.clip(6.0-4.0*score/100.0,2.0,6.0))


def build_complete_portfolio(orp_weights,expected_returns,covariance,risk_free_rate,risk_tolerance,allow_leverage=None,margin_rate=None,max_leverage=2.0,current_weights=None,regime=None,equity_min=None,equity_max=None,max_single_stock_weight=1.0,profile_equity_min=None,profile_equity_max=None,**kwargs):
    session_policy={};widget_leverage=None;widget_margin=None
    try:
        import streamlit as st
        session_policy=st.session_state.get('policy') or {}
        widget_leverage=st.session_state.get('allow_leverage',None);widget_margin=st.session_state.get('margin_rate',None)
    except Exception: st=None
    if allow_leverage is None:allow_leverage=bool(widget_leverage if widget_leverage is not None else session_policy.get('allow_leverage',False))
    if margin_rate is None:
        if widget_margin is not None:margin_rate=float(widget_margin/100)
        elif 'saved_margin_rate' in (st.session_state if st is not None else {}):margin_rate=float(st.session_state['saved_margin_rate'])
        else:margin_rate=float(session_policy.get('margin_rate',0.12))
    if profile_equity_min is None or profile_equity_max is None:profile_equity_min,profile_equity_max=equity_frame_from_profile(session_policy or {'risk_capacity':risk_tolerance})
    if equity_min is None or equity_max is None:equity_min,equity_max=profile_equity_min,profile_equity_max
    budget_min,budget_max,budget_source=combine_equity_budgets(profile_equity_min,profile_equity_max,equity_min,equity_max)
    w_orp=pd.Series(orp_weights,dtype=float).clip(lower=0)
    if w_orp.sum()<=0:raise ValueError('Danh mục cổ phiếu không có tỷ trọng hợp lệ.')
    w_orp=w_orp/w_orp.sum();mu=pd.Series(expected_returns,dtype=float).reindex(w_orp.index).fillna(0);cov=pd.DataFrame(covariance,dtype=float).reindex(index=w_orp.index,columns=w_orp.index).fillna(0)
    rf=float(risk_free_rate);margin=float(margin_rate);A=risk_aversion_from_profile(risk_tolerance)
    er_orp=float(w_orp.dot(mu));variance_orp=float(w_orp.dot(cov).dot(w_orp));sigma_orp=float(np.sqrt(max(variance_orp,0.0)))
    raw_no_borrow=float((er_orp-rf)/(A*variance_orp)) if variance_orp>1e-12 else 0.0
    raw_with_margin=float((er_orp-margin)/(A*variance_orp)) if allow_leverage and variance_orp>1e-12 else raw_no_borrow
    raw_y=float(np.clip(raw_with_margin,0.0,float(max_leverage))) if allow_leverage else float(np.clip(raw_no_borrow,0.0,1.0))
    y=float(np.clip(raw_y,budget_min,budget_max))
    if not allow_leverage:y=min(y,1.0)
    complete_equity=w_orp*y;borrowed=max(0.0,y-1.0);defensive=max(0.0,1.0-y);borrowing_cost=borrowed*margin
    complete_return=y*er_orp-borrowed*margin+defensive*rf;complete_vol=abs(y)*sigma_orp;complete_sharpe=(complete_return-rf)/complete_vol if complete_vol>1e-12 else np.nan
    comparison=compare_current_to_target(current_weights if current_weights is not None else pd.Series(dtype=float),complete_equity)
    return {'orp_weights':w_orp,'complete_equity_weights':complete_equity,'defensive_weight':defensive,'borrowed_weight':borrowed,'expected_return_orp':er_orp,'volatility_orp':sigma_orp,'variance_orp':variance_orp,'risk_free_rate':rf,'margin_rate':margin,'risk_aversion':A,'y_raw_no_borrow':raw_no_borrow,'y_raw_with_margin':raw_with_margin,'y_unconstrained':raw_y,'y':y,'complete_expected_return':complete_return,'complete_volatility':complete_vol,'complete_sharpe':complete_sharpe,'borrowing_cost':borrowing_cost,'allow_leverage':bool(allow_leverage),'max_leverage':float(max_leverage),'regime':regime,'equity_min':float(equity_min),'equity_max':float(equity_max),'profile_equity_min':float(profile_equity_min),'profile_equity_max':float(profile_equity_max),'final_equity_min':budget_min,'final_equity_max':budget_max,'budget_source':budget_source,'comparison':comparison}


def build_recommendation(current_weights,target_weights,regime,equity_min,equity_max,max_single_stock_weight=1.0,complete_portfolio=None):
    target=pd.Series(target_weights,dtype=float).clip(lower=0)
    if target.sum()==0:raise ValueError('Danh mục mục tiêu không có tỷ trọng hợp lệ.')
    target=target/target.sum();max_single=float(max_single_stock_weight)
    if complete_portfolio is not None:
        adjusted=pd.Series(complete_portfolio['complete_equity_weights'],dtype=float);defensive=float(complete_portfolio['defensive_weight']);borrowed=float(complete_portfolio['borrowed_weight'])
    else:
        adjusted=target*((float(equity_min)+float(equity_max))/2);defensive=max(0.,1-adjusted.sum());borrowed=0.0
    if adjusted.max()>max_single+1e-8:raise ValueError(f'Danh mục có tỷ trọng cổ phiếu {adjusted.max():.2%}, vượt giới hạn {max_single:.2%}.')
    return {'target_equity_weights':adjusted,'defensive_weight':defensive,'borrowed_weight':borrowed,'comparison':compare_current_to_target(current_weights,adjusted),'regime':regime,'complete_portfolio':complete_portfolio}
