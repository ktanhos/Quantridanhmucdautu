import streamlit as st
from portfolio_holdings import build_holdings_table,holdings_to_weights

def render_holdings(prices):
    st.header('Bước 6. Danh mục thực tế')
    st.caption('Nhập số lượng cổ phiếu đang nắm giữ. Hệ thống tự lấy giá hiện tại từ dữ liệu đã tải và tính giá trị thị trường cùng tỷ trọng thực tế.')
    tickers=list(prices.columns);holdings=[];cols=st.columns(min(4,len(tickers)))
    for i,ticker in enumerate(tickers):
        with cols[i%len(cols)]:qty=st.number_input(f'{ticker} — Số lượng',min_value=0.,value=0.,step=100.,key=f'holding_qty_{ticker}')
        holdings.append({'ticker':ticker,'quantity':qty})
    if st.button('CẬP NHẬT DANH MỤC THỰC TẾ',type='primary',use_container_width=True):st.session_state['holdings_input']=holdings
    holdings=st.session_state.get('holdings_input',holdings);table=build_holdings_table(holdings,prices)
    if table.empty:st.info('Chưa có cổ phiếu nào được nhập.')
    else:
        st.subheader('6.1. Cơ cấu danh mục thực tế');display=table.copy();display['Giá hiện tại']=display['Giá hiện tại'].map(lambda x:f'{x:,.0f}');display['Giá trị thị trường']=display['Giá trị thị trường'].map(lambda x:f'{x:,.0f}');display['Tỷ trọng']=display['Tỷ trọng'].map(lambda x:f'{x:.2%}');st.dataframe(display,use_container_width=True,hide_index=True);st.session_state['current_weights']=holdings_to_weights(table)
    return table
