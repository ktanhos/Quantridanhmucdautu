import numpy as np
import pandas as pd
import streamlit as st

def _stats(r):
    r=pd.Series(r,dtype=float).dropna()
    if r.empty:return {'Cumulative Return':np.nan,'Annualized Return':np.nan,'Annualized Volatility':np.nan,'Sharpe Ratio':np.nan,'Maximum Drawdown':np.nan}
    wealth=(1+r).cumprod();years=len(r)/252;ann=wealth.iloc[-1]**(1/years)-1 if years>0 else np.nan;vol=r.std(ddof=1)*np.sqrt(252);sh=ann/vol if vol>0 else np.nan;dd=(wealth/wealth.cummax()-1).min();return {'Cumulative Return':wealth.iloc[-1]-1,'Annualized Return':ann,'Annualized Volatility':vol,'Sharpe Ratio':sh,'Maximum Drawdown':dd}

def render_portfolio_performance(returns,benchmark_returns=None,current_weights=None):
    st.header('Bước 10. Đánh giá hiệu quả danh mục');st.caption('Đánh giá hiệu quả lịch sử từ dữ liệu giá đã có. Không sử dụng lịch sử giao dịch và không giả định chi phí phát sinh theo từng lệnh.')
    if current_weights is not None and not current_weights.empty:
        w=current_weights.reindex(returns.columns).fillna(0);w=w/w.sum() if w.sum()>0 else w;portfolio=returns.mul(w,axis=1).sum(axis=1)
    else:portfolio=returns.mean(axis=1)
    p=_stats(portfolio);b=_stats(benchmark_returns) if benchmark_returns is not None else None;st.session_state['portfolio_performance']=p
    st.subheader('10.1. Các chỉ tiêu chính');c1,c2,c3,c4=st.columns(4);c1.metric('Lợi suất tích lũy',f'{p["Cumulative Return"]:.2%}');c2.metric('Lợi suất năm hóa',f'{p["Annualized Return"]:.2%}');c3.metric('Sharpe Ratio',f'{p["Sharpe Ratio"]:.2f}');c4.metric('Maximum Drawdown',f'{p["Maximum Drawdown"]:.2%}')
    rows=[['Danh mục',p['Cumulative Return'],p['Annualized Return'],p['Annualized Volatility'],p['Sharpe Ratio'],p['Maximum Drawdown']]]
    if b:rows.append(['VNINDEX',b['Cumulative Return'],b['Annualized Return'],b['Annualized Volatility'],b['Sharpe Ratio'],b['Maximum Drawdown']])
    table=pd.DataFrame(rows,columns=['Đối tượng','Lợi suất tích lũy','Lợi suất năm hóa','Độ biến động năm hóa','Sharpe Ratio','Maximum Drawdown'])
    for col in ['Lợi suất tích lũy','Lợi suất năm hóa','Độ biến động năm hóa','Maximum Drawdown']:table[col]=table[col].map(lambda x:'N/A' if pd.isna(x) else f'{x:.2%}')
    table['Sharpe Ratio']=table['Sharpe Ratio'].map(lambda x:'N/A' if pd.isna(x) else f'{x:.2f}')
    st.subheader('10.2. So sánh với VNINDEX');st.dataframe(table,use_container_width=True,hide_index=True);st.info('Các chỉ tiêu phản ánh kết quả lịch sử của giai đoạn dữ liệu đã chọn, không phải dự báo lợi nhuận tương lai.')
