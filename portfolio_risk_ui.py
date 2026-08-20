import numpy as np
import pandas as pd
import streamlit as st
from portfolio_risk import calculate_portfolio_risk

def _fmt(x,kind='ratio'):
    if pd.isna(x) or not np.isfinite(x):return 'N/A'
    return f'{x:.2%}' if kind=='pct' else f'{x:.2f}'

def render_portfolio_risk(returns,benchmark_returns,risk_free_rate=0.0):
    st.subheader('4.1. Bức tranh rủi ro của tập cổ phiếu')
    st.markdown('<div class="section-note">Mục tiêu là xem các cổ phiếu có bổ sung cho nhau hay đang cùng mang một loại rủi ro. Một mã tốt riêng lẻ chưa chắc giúp danh mục tốt hơn.</div>',unsafe_allow_html=True)
    tickers=list(returns.columns)
    if len(tickers)<2:st.warning('Cần ít nhất 2 mã cổ phiếu để xem lợi ích đa dạng hóa.');return
    weights=pd.Series(1/len(tickers),index=tickers,dtype=float)
    try:result=calculate_portfolio_risk(returns,weights,benchmark_returns,risk_free_rate)
    except Exception as exc:st.error(f'Không thể phân tích tập cổ phiếu: {exc}');return
    c1,c2,c3,c4=st.columns(4);c1.metric('Lợi suất lịch sử quy đổi năm',_fmt(result['annual_return'],'pct'));c2.metric('Mức biến động',_fmt(result['annual_volatility'],'pct'));c3.metric('Hiệu quả trên mức biến động',_fmt(result['sharpe']));c4.metric('Mức giảm lớn nhất',_fmt(result['max_drawdown'],'pct'))
    st.caption('Các số liệu trên dùng tỷ trọng chia đều chỉ để nhìn đặc điểm chung của tập cổ phiếu. Đây chưa phải danh mục cuối cùng.')
    st.subheader('4.2. Mã nào đang đóng góp nhiều rủi ro hơn?')
    rc=result['risk_contribution'].sort_values(ascending=False).rename('Đóng góp rủi ro').to_frame();rc['Tỷ trọng tham chiếu']=result['weights'];view=rc.copy();view['Đóng góp rủi ro']=view['Đóng góp rủi ro'].map(lambda x:f'{x:.2%}');view['Tỷ trọng tham chiếu']=view['Tỷ trọng tham chiếu'].map(lambda x:f'{x:.2%}');st.dataframe(view,use_container_width=True)
    st.caption('Hai mã có thể được chia tiền bằng nhau nhưng không gây ra cùng mức rủi ro. Mã đóng góp rủi ro lớn hơn sẽ được kiểm tra kỹ ở bước phân bổ.')
    with st.expander('4.3. Các cổ phiếu biến động cùng nhau ra sao?',expanded=False):
        st.dataframe(result['correlation'].round(3),use_container_width=True);st.caption('Nếu nhiều cổ phiếu thường tăng giảm cùng lúc, mua thêm mã chưa chắc giúp đa dạng hóa. Tương quan thấp có thể giúp phân tán rủi ro nhưng không bảo đảm khi thị trường biến động mạnh.')
    with st.expander('Giải thích các chỉ tiêu',expanded=False):
        st.markdown('**Sharpe Ratio**: với mức lên xuống đã chịu, lợi nhuận có tương xứng không.\n\n**Sortino Ratio**: tương tự Sharpe nhưng chú ý nhiều hơn đến những giai đoạn giảm.\n\n**Information Ratio**: nếu danh mục khác VNINDEX, phần kết quả tốt hơn có đáng với mức khác biệt đó không.\n\n**Jensen Alpha**: ước tính phần lợi nhuận còn lại sau khi đã tính đến mức danh mục thường đi cùng thị trường.\n\n**Treynor Ratio**: nhìn lợi nhuận so với phần rủi ro đến từ biến động chung của thị trường.')
