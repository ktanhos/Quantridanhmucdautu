import streamlit as st
import pandas as pd
from portfolio_after_costs import calculate_after_cost_returns,performance_summary

def render_after_costs(returns,benchmark_returns=None):
    st.header('Bước 10. Đánh giá hiệu quả sau chi phí')
    st.caption('Ước tính tác động của phí giao dịch và thuế lên lợi suất danh mục. Phí lưu ký và chi phí Margin được hiển thị riêng vì cần dữ liệu thực tế.')
    fee_rate=0.001;sell_tax_rate=0.001;turnover=returns.abs().sum(axis=1)/len(returns.columns);gross=returns.mean(axis=1);after=calculate_after_cost_returns(gross,turnover,fee_rate,sell_tax_rate);summary=performance_summary(gross,after,benchmark_returns)
    rows=[]
    for name in ['Trước chi phí','Sau chi phí']:
        s=summary[name];rows.append({'Chỉ tiêu':name,'Lợi suất năm':s['Annualized Return'],'Độ biến động':s['Annualized Volatility'],'Sharpe Ratio':s['Sharpe Ratio'],'Maximum Drawdown':s['Maximum Drawdown']})
    table=pd.DataFrame(rows)
    for col in ['Lợi suất năm','Độ biến động','Maximum Drawdown']:table[col]=table[col].map(lambda x:f'{x:.2%}')
    table['Sharpe Ratio']=table['Sharpe Ratio'].map(lambda x:f'{x:.2f}')
    st.subheader('10.1. Hiệu quả trước và sau chi phí');st.dataframe(table,use_container_width=True,hide_index=True)
    gross_ann=summary['Trước chi phí']['Annualized Return'];net_ann=summary['Sau chi phí']['Annualized Return'];c1,c2,c3=st.columns(3);c1.metric('Lợi suất năm trước chi phí',f'{gross_ann:.2%}');c2.metric('Lợi suất năm sau chi phí',f'{net_ann:.2%}');c3.metric('Tác động chi phí',f'{net_ann-gross_ann:.2%}')
    st.subheader('10.2. Cơ cấu chi phí sử dụng trong mô hình');costs=pd.DataFrame([['Phí giao dịch mua/bán','0,10%','Tính theo giá trị giao dịch'],['Thuế khi bán','0,10%','Tính theo giá trị bán'],['Phí lưu ký','0,27 đồng/cổ phiếu/tháng','Chưa đưa vào lợi suất do chưa có lịch sử số lượng theo thời gian'],['Lãi suất Margin','12%/năm','Chỉ phát sinh khi bật vay Margin']],columns=['Khoản mục','Giả định','Cách xử lý']);st.dataframe(costs,use_container_width=True,hide_index=True)
    st.info('Ước tính hiện tại dùng turnover xấp xỉ từ biến động lợi suất để minh họa tác động chi phí. Khi có lịch sử giao dịch thực tế, chi phí sẽ được tính trực tiếp theo từng giao dịch.')
