from __future__ import annotations
import pandas as pd

def calculate_rebalancing(current_weights,target_weights,threshold=0.05):
    current=pd.Series(current_weights,dtype=float);target=pd.Series(target_weights,dtype=float);names=current.index.union(target.index);current=current.reindex(names).fillna(0);target=target.reindex(names).fillna(0)
    if current.sum()>0:current=current/current.sum()
    if target.sum()>0:target=target/target.sum()
    out=pd.DataFrame({'Tỷ trọng hiện tại':current,'Tỷ trọng mục tiêu':target});out['Độ lệch']=out['Tỷ trọng hiện tại']-out['Tỷ trọng mục tiêu'];out['Cần tái cân bằng']=out['Độ lệch'].abs()>=threshold;out['Hành động']='Giữ nguyên';out.loc[out['Độ lệch']>threshold,'Hành động']='Giảm tỷ trọng';out.loc[out['Độ lệch']<-threshold,'Hành động']='Tăng tỷ trọng';return out.sort_values('Độ lệch',ascending=False)

def rebalance_summary(table):
    flagged=table[table['Cần tái cân bằng']];return {'count':len(flagged),'max_deviation':float(table['Độ lệch'].abs().max()),'needs_rebalance':not flagged.empty}
