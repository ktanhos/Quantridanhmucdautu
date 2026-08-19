from __future__ import annotations
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
