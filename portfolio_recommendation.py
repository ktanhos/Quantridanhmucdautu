from __future__ import annotations
import pandas as pd

def compare_current_to_target(current_weights,target_weights):
    current=pd.Series(current_weights,dtype=float);target=pd.Series(target_weights,dtype=float)
    names=current.index.union(target.index);current=current.reindex(names).fillna(0);target=target.reindex(names).fillna(0)
    current=current/current.sum() if current.sum()!=0 else current;target=target/target.sum() if target.sum()!=0 else target
    out=pd.DataFrame({'Tỷ trọng hiện tại':current,'Tỷ trọng mục tiêu':target});out['Thay đổi tỷ trọng']=out['Tỷ trọng mục tiêu']-out['Tỷ trọng hiện tại'];return out.sort_values('Thay đổi tỷ trọng',ascending=False)

def regime_adjustment(weights,regime,equity_min,equity_max):
    w=pd.Series(weights,dtype=float).clip(lower=0)
    if w.sum()==0:return w
    return w/w.sum()*((equity_min+equity_max)/2)

def build_recommendation(current_weights,target_weights,regime,equity_min,equity_max):
    target=pd.Series(target_weights,dtype=float).clip(lower=0)
    if target.sum()==0:raise ValueError('Danh mục mục tiêu không có tỷ trọng hợp lệ.')
    target=target/target.sum();adjusted=regime_adjustment(target,regime,equity_min,equity_max);defensive=max(0.,1-adjusted.sum())
    return {'target_equity_weights':adjusted,'defensive_weight':defensive,'comparison':compare_current_to_target(current_weights,adjusted),'regime':regime}
