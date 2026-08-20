import numpy as np
import pandas as pd
import streamlit as st
from portfolio_risk import calculate_portfolio_risk


def _fmt_pct(x): return 'N/A' if pd.isna(x) else f'{x:.2%}'
def _fmt_ratio(x): return 'N/A' if pd.isna(x) or not np.isfinite(x) else f'{x:.2f}'

def _portfolio_weights(current_weights, columns):
    if current_weights is None:return None
    if np.isscalar(current_weights):return None
    try:
        w=pd.Series(current_weights,dtype=float).reindex(columns).fillna(0)
        return w if len(w)>0 and w.sum()>0 else None
    except Exception:return None

def render_portfolio_performance(returns,benchmark_returns=None,current_weights=None,risk_free_rate=0.0):
    st.header('Bước 7. Đánh giá hiệu quả lịch sử danh mục')
    st.markdown('<div class="section-note">Đánh giá trên dữ liệu quá khứ: danh mục đã tăng giảm ra sao, mức rủi ro phải chịu và kết quả so với VNINDEX. Đây là nhìn lại lịch sử, không phải dự báo tương lai.</div>',unsafe_allow_html=True)
    leverage=st.session_state.get('complete_portfolio_result') or {};borrowed=float(leverage.get('borrowed_weight',0.0));margin_rate=float(leverage.get('margin_rate',0.0));leveraged=borrowed>1e-10
    w=_portfolio_weights(current_weights,returns.columns)
    if w is None:
        candidate=leverage.get('complete_equity_weights')
        w=_portfolio_weights(candidate,returns.columns)
    if w is not None:
        if leveraged:portfolio=returns.mul(w,axis=1).sum(axis=1)-borrowed*margin_rate/252;label='Danh mục đề xuất có sử dụng tiền vay'
        else:w=w/w.sum();portfolio=returns.mul(w,axis=1).sum(axis=1);label='Danh mục đề xuất'
    else:
        w=pd.Series(1/len(returns.columns),index=returns.columns);portfolio=returns.mul(w,axis=1).sum(axis=1);label='Tập cổ phiếu bình quân'
    portfolio=portfolio.replace([np.inf,-np.inf],np.nan).dropna()
    p=calculate_portfolio_risk(pd.DataFrame({'Portfolio':portfolio}),pd.Series({'Portfolio':1.0}),benchmark_returns,risk_free_rate)
    b=calculate_portfolio_risk(pd.DataFrame({'VNINDEX':benchmark_returns}),pd.Series({'VNINDEX':1.0}),None,risk_free_rate) if benchmark_returns is not None else None
    st.session_state['portfolio_performance']={'Cumulative Return':float((1+p['portfolio_returns']).prod()-1),'Annualized Return':p['annual_return'],'Annualized Volatility':p['annual_volatility'],'Sharpe Ratio':p['sharpe'],'Maximum Drawdown':p['max_drawdown']}
    if leveraged:st.warning(f'Kết quả đã trừ chi phí vay giả định {margin_rate:.2%}/năm trên phần vốn vay {borrowed:.1%}. Lãi suất thực tế có thể thay đổi.')
    st.subheader('Kết quả chính');c1,c2,c3,c4=st.columns(4);c1.metric('Lợi suất tích lũy',_fmt_pct(st.session_state['portfolio_performance']['Cumulative Return']));c2.metric('Lợi suất quy đổi theo năm',_fmt_pct(p['annual_return']));c3.metric('Hiệu quả trên rủi ro tổng thể',_fmt_ratio(p['sharpe']));c4.metric('Mức giảm lớn nhất',_fmt_pct(p['max_drawdown']))
    st.subheader('Nhìn danh mục từ nhiều góc độ');c1,c2,c3,c4=st.columns(4);c1.metric('Hiệu quả khi chỉ tính rủi ro giảm giá',_fmt_ratio(p['sortino']));c2.metric('Chất lượng phần lợi nhuận vượt VNINDEX',_fmt_ratio(p['information_ratio']));c3.metric('Phần lợi nhuận vượt mức thị trường giải thích',_fmt_pct(p['jensen_alpha']));c4.metric('Mức khác biệt so với VNINDEX',_fmt_pct(p['tracking_error']))
    with st.expander('Các chỉ tiêu này nói gì?',expanded=True):
        st.markdown('• **Sharpe Ratio** trả lời: với mức lên xuống đã phải chịu, lợi nhuận của danh mục có tương xứng không.\n\n• **Sortino Ratio** chỉ quan tâm nhiều hơn đến những giai đoạn danh mục giảm, nên phù hợp khi bạn lo về rủi ro thua lỗ hơn là mọi biến động.\n\n• **Information Ratio** trả lời: nếu danh mục làm tốt hơn VNINDEX, phần tốt hơn đó có đáng so với mức khác biệt và rủi ro đã chấp nhận hay không.\n\n• **Jensen Alpha** ước tính phần lợi nhuận còn lại sau khi đã tính đến mức độ danh mục đi cùng thị trường. Giá trị dương nghĩa là trong mô hình đang dùng, kết quả tốt hơn mức thị trường giải thích.\n\n• **Treynor Ratio** xem lợi nhuận so với rủi ro đến từ biến động chung của thị trường.\n\nKhông chỉ tiêu nào một mình quyết định danh mục tốt hay xấu.')
        c1,c2,c3,c4=st.columns(4);c1.metric('Beta so với VNINDEX',_fmt_ratio(p['beta']));c2.metric('Treynor Ratio',_fmt_ratio(p['treynor']));c3.metric('Mức điều chỉnh theo rủi ro tổng thể',_fmt_pct(p['m2']));c4.metric('Mức độ đi cùng VNINDEX',_fmt_pct(p['r_squared']))
    if benchmark_returns is not None:
        st.subheader('So sánh với VNINDEX');rows=[[label,p['annual_return'],p['annual_volatility'],p['sharpe'],p['max_drawdown']],['VNINDEX',b['annual_return'],b['annual_volatility'],b['sharpe'],b['max_drawdown']]];table=pd.DataFrame(rows,columns=['Đối tượng','Lợi suất quy đổi theo năm','Biến động quy đổi theo năm','Sharpe Ratio','Maximum Drawdown'])
        for col in ['Lợi suất quy đổi theo năm','Biến động quy đổi theo năm','Maximum Drawdown']:table[col]=table[col].map(_fmt_pct)
        table['Sharpe Ratio']=table['Sharpe Ratio'].map(_fmt_ratio);st.dataframe(table,use_container_width=True,hide_index=True)
    st.subheader('Đọc kết quả');st.write('Hãy nhìn đồng thời lợi suất, mức giảm lớn nhất và kết quả so với VNINDEX. Một danh mục có lợi nhuận cao nhưng từng giảm quá sâu vẫn có thể không phù hợp với khả năng chịu rủi ro của bạn.')
