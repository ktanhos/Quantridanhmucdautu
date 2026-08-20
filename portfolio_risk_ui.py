import numpy as np
import pandas as pd
import streamlit as st
from portfolio_risk import calculate_portfolio_risk

def _fmt(x,kind='ratio'):
    if pd.isna(x) or not np.isfinite(x):return 'N/A'
    return f'{x:.2%}' if kind=='pct' else f'{x:.2f}'

def render_portfolio_risk(returns,benchmark_returns,risk_free_rate=0.0):
    st.subheader('Bước 4. Chọn cổ phiếu phù hợp')
    st.markdown('<div class="section-note">Đây là bước kiểm tra cả tập cổ phiếu trước khi chia tiền. Mục tiêu không phải tìm một mã chắc chắn tăng, mà xem các mã khi đứng cùng nhau có tạo ra một danh mục đa dạng và phù hợp với mức rủi ro hay không.</div>',unsafe_allow_html=True)
    tickers=list(returns.columns)
    if len(tickers)<2:st.warning('Cần ít nhất 2 mã cổ phiếu để xem lợi ích đa dạng hóa.');return
    weights=pd.Series(1/len(tickers),index=tickers,dtype=float)
    try:result=calculate_portfolio_risk(returns,weights,benchmark_returns,risk_free_rate)
    except Exception as exc:st.error(str(exc));return
    st.subheader('Bức tranh nhanh của tập cổ phiếu');c1,c2,c3,c4=st.columns(4);c1.metric('Lợi suất lịch sử quy đổi năm',_fmt(result['annual_return'],'pct'));c2.metric('Mức biến động',_fmt(result['annual_volatility'],'pct'));c3.metric('Hiệu quả trên mức biến động',_fmt(result['sharpe']));c4.metric('Mức giảm lớn nhất',_fmt(result['max_drawdown'],'pct'))
    st.subheader('Các mã có đang cùng chịu một loại rủi ro không?');rc=result['risk_contribution'].sort_values(ascending=False).rename('Đóng góp rủi ro').to_frame();rc['Tỷ trọng tham chiếu']=result['weights'];view=rc.copy();view['Đóng góp rủi ro']=view['Đóng góp rủi ro'].map(lambda x:f'{x:.2%}');view['Tỷ trọng tham chiếu']=view['Tỷ trọng tham chiếu'].map(lambda x:f'{x:.2%}');st.dataframe(view,use_container_width=True)
    st.caption('Một mã có thể chiếm tỷ trọng giống các mã khác nhưng lại đóng góp nhiều rủi ro hơn. Đây là lý do bước tiếp theo không chia tiền chỉ dựa trên mức kỳ vọng tăng giá.')
    with st.expander('Xem các cổ phiếu biến động cùng nhau như thế nào',expanded=True):
        st.dataframe(result['correlation'].round(3),use_container_width=True);st.caption('Nếu nhiều cổ phiếu thường tăng giảm cùng lúc, việc mua tất cả chưa chắc giúp danh mục an toàn hơn. Tương quan thấp hơn thường tạo thêm lợi ích đa dạng hóa, nhưng không bảo đảm trong mọi giai đoạn.')
    with st.expander('Các chỉ tiêu khác nói gì?',expanded=False):
        st.markdown('• **Sharpe Ratio** cho biết lợi nhuận đạt được có tương xứng với mức lên xuống của danh mục không.\n\n• **Sortino Ratio** tập trung nhiều hơn vào những giai đoạn giảm giá.\n\n• **Information Ratio** cho biết phần kết quả tốt hơn hoặc kém hơn VNINDEX có đáng so với mức rủi ro khác biệt đã chấp nhận hay không.\n\n• **Jensen Alpha** ước tính phần kết quả vượt ra ngoài mức có thể giải thích chỉ bằng việc danh mục đi cùng thị trường.\n\n• **Treynor Ratio** xem lợi nhuận so với phần rủi ro đến từ biến động chung của thị trường.')
    with st.expander('Diễn giải Sharpe',expanded=True):
        if np.isfinite(result['sharpe']):st.write(f'Chỉ tiêu hiện tại là {result["sharpe"]:.2f}. Nó cho biết với mức biến động đã chịu, danh mục tạo ra lợi nhuận vượt lãi suất tham chiếu đến đâu. Nên dùng để so sánh các phương án trong cùng bối cảnh, không nên chỉ nhìn một con số để kết luận tốt hay xấu.')
        st.write(f'Lãi suất tham chiếu đang dùng là {risk_free_rate:.2%} mỗi năm.')
        st.write('Ngoài chỉ tiêu này, hãy xem mức giảm lớn nhất để biết danh mục từng mất bao nhiêu từ đỉnh xuống đáy và xem CVaR để hình dung mức thua lỗ trong những ngày xấu.')
