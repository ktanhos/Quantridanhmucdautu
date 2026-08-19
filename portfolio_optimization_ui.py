import streamlit as st
from portfolio_optimization import optimize_portfolios

def render_portfolio_optimization(returns,policy):
    st.header('Bước 7. Tối ưu hóa danh mục')
    st.caption('Xây dựng các danh mục mục tiêu từ dữ liệu lịch sử và giới hạn rủi ro trong Hồ sơ đầu tư. Đây là kết quả mô hình, không phải khuyến nghị mua bán.')
    max_weight=float(policy.get('max_single_stock_weight',0.10)) if policy else 0.10
    target=float(policy.get('target_return',0)) if policy else None
    try:result=optimize_portfolios(returns,max_weight=max_weight,target_return=target)
    except Exception as exc:st.error(str(exc));return
    st.subheader('7.1. So sánh các danh mục mô hình')
    summary=result['summary'].copy();summary['Lợi suất kỳ vọng']=summary['Lợi suất kỳ vọng'].map(lambda x:f'{x:.2%}');summary['Độ biến động']=summary['Độ biến động'].map(lambda x:f'{x:.2%}');summary['Sharpe Ratio']=summary['Sharpe Ratio'].map(lambda x:f'{x:.2f}');st.dataframe(summary,use_container_width=True)
    st.subheader('7.2. Phân bổ tài sản theo danh mục')
    weights=result['weights'].copy();weights=weights[weights.max(axis=1)>1e-6];display=weights.copy()
    for col in display.columns:display[col]=display[col].map(lambda x:f'{x:.2%}')
    st.dataframe(display,use_container_width=True)
    selected=st.selectbox('Danh mục mô hình muốn xem sâu',['Minimum Variance','Optimal Risky','Maximum Return'])
    st.markdown(f'**Bảng 7.1. Tỷ trọng {selected}**')
    selected_weights=weights[selected].sort_values(ascending=False);selected_table=selected_weights[selected_weights>1e-6].rename('Tỷ trọng').to_frame();selected_table['Tỷ trọng']=selected_table['Tỷ trọng'].map(lambda x:f'{x:.2%}');st.dataframe(selected_table,use_container_width=True)
    st.caption('Maximum Return chọn cổ phiếu có lợi suất lịch sử cao nhất và bị giới hạn bởi tỷ trọng tối đa. Optimal Risky tìm kiếm theo Sharpe Ratio. Minimum Variance ưu tiên giảm phương sai.')
    st.session_state['optimization_result']=result
