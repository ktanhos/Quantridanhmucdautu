from __future__ import annotations
import pandas as pd

def build_holdings_table(holdings, prices):
    rows=[];latest=prices.iloc[-1]
    for item in holdings:
        ticker=str(item.get('ticker','')).strip().upper();qty=float(item.get('quantity',0) or 0);price=float(latest.get(ticker,0) or 0)
        if qty>0 and price>0:rows.append({'Mã cổ phiếu':ticker,'Số lượng':qty,'Giá hiện tại':price,'Giá trị thị trường':qty*price})
    table=pd.DataFrame(rows)
    if table.empty:return table
    total=table['Giá trị thị trường'].sum();table['Tỷ trọng']=table['Giá trị thị trường']/total if total else 0
    return table.sort_values('Tỷ trọng',ascending=False).reset_index(drop=True)

def holdings_to_weights(table):
    if table is None or table.empty:return pd.Series(dtype=float)
    return table.set_index('Mã cổ phiếu')['Tỷ trọng'].astype(float)
