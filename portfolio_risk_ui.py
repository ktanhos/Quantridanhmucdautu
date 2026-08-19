import numpy as np
import pandas as pd
import streamlit as st
from portfolio_risk import calculate_portfolio_risk

def render_portfolio_risk(returns, benchmark_returns):
    st.header('Bước 6. Đánh giá rủi ro danh mục')
    st.caption('Đánh giá danh mục hiện tại trước khi tối ưu hóa. Tất cả chỉ tiêu sử dụng dữ liệu ngày.')
    tickers=list(returns.columns)
    st.subheader('6.1. Tỷ trọng danh mục hiện tại')
    default=np.repeat(1/len(tickers),len(tickers));weights={};cols=st.columns(min(4,len(tickers)))
    for i,ticker in enumerate(tickers):
        with cols[i%len(cols)]:weights[ticker]=st.number_input(f'{ticker} (%)',0.,100.,float(default[i]*100),1.,key=f'risk_weight_{ticker}')/100
    st.caption(f'Tổng tỷ trọng nhập vào: {sum(weights.values()):.1%}. Hệ thống chuẩn hóa về 100% để tính toán.')
    try:result=calculate_portfolio_risk(returns,pd.Series(weights),benchmark_returns)
    except Exception as exc:st.error(str(exc));return
    st.subheader('6.2. Tổng quan rủi ro và lợi suất')
    c1,c2,c3,c4=st.columns(4);c1.metric('Lợi suất năm hóa',f'{result["annual_return"]:.2%}');c2.metric('Độ biến động năm hóa',f'{result["annual_volatility"]:.2%}');c3.metric('Sharpe Ratio',f'{result["sharpe"]:.2f}');c4.metric('Maximum Drawdown',f'{result["max_drawdown"]:.2%}')
    c1,c2,c3,c4=st.columns(4);c1.metric('VaR 95% theo ngày',f'{result["var_95_daily"]:.2%}');c2.metric('CVaR 95% theo ngày',f'{result["cvar_95_daily"]:.2%}');c3.metric('Beta với VNINDEX',f'{result["beta"]:.2f}' if np.isfinite(result['beta']) else 'N/A');c4.metric('Information Ratio',f'{result["information_ratio"]:.2f}' if np.isfinite(result['information_ratio']) else 'N/A')
    st.markdown('**Bảng 6.1. Đóng góp rủi ro của từng cổ phiếu**')
    rc=result['risk_contribution'].sort_values(ascending=False).rename('Đóng góp rủi ro');table=rc.to_frame();table['Tỷ trọng']=result['weights'];table['Đóng góp rủi ro']=table['Đóng góp rủi ro'].map(lambda x:f'{x:.2%}');table['Tỷ trọng']=table['Tỷ trọng'].map(lambda x:f'{x:.2%}');st.dataframe(table,use_container_width=True)
    st.markdown('**Bảng 6.2. Tương quan giữa các cổ phiếu**');st.dataframe(result['correlation'].round(3),use_container_width=True)
    st.markdown('**Bảng 6.3. Mức độ tập trung danh mục**');st.metric('Herfindahl Hirschman Index',f'{result["concentration_hhi"]:.3f}');st.caption('HHI càng cao thì danh mục càng tập trung. Đây là phân tích danh mục hiện tại, chưa phải danh mục tối ưu.')
