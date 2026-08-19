import streamlit as st
from portfolio_rebalancing import calculate_rebalancing,rebalance_summary

def render_rebalancing(current_weights,optimization_result):
    st.header('Bước 9. Theo dõi và tái cân bằng')
    st.caption('Đánh giá mức lệch giữa danh mục thực tế và danh mục mục tiêu. Ngưỡng tái cân bằng mặc định là 5 điểm phần trăm.')
    if not optimization_result:return
    model=st.selectbox('Danh mục mục tiêu',['Optimal Risky','Minimum Variance','Maximum Return'],key='rebalance_model');target=optimization_result['weights'][model]
    if current_weights is None or current_weights.empty:st.warning('Chưa có danh mục thực tế. Hãy nhập số lượng cổ phiếu ở Bước 6.');return
    threshold=st.slider('Ngưỡng tái cân bằng',1,15,5,1)/100;table=calculate_rebalancing(current_weights,target,threshold);summary=rebalance_summary(table)
    st.subheader('9.1. Trạng thái danh mục');c1,c2,c3=st.columns(3);c1.metric('Mức lệch lớn nhất',f'{summary["max_deviation"]:.2%}');c2.metric('Số mã cần điều chỉnh',summary['count']);c3.metric('Trạng thái','Cần tái cân bằng' if summary['needs_rebalance'] else 'Đang trong ngưỡng')
    display=table.copy();display['Tỷ trọng hiện tại']=display['Tỷ trọng hiện tại'].map(lambda x:f'{x:.2%}');display['Tỷ trọng mục tiêu']=display['Tỷ trọng mục tiêu'].map(lambda x:f'{x:.2%}');display['Độ lệch']=display['Độ lệch'].map(lambda x:f'{x:+.2%}');st.dataframe(display,use_container_width=True)
    st.subheader('9.2. Hành động đề xuất');actions=table[table['Cần tái cân bằng']]
    if actions.empty:st.success('Không có cổ phiếu nào vượt ngưỡng tái cân bằng.')
    else:
        for ticker,row in actions.iterrows():st.write(f'{ticker}: {row["Hành động"]} {abs(row["Độ lệch"]):.2%}')
    st.caption('Tái cân bằng chỉ được kích hoạt khi độ lệch tuyệt đối vượt ngưỡng do người dùng đặt. Hệ thống không thực hiện giao dịch.')
