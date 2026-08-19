import math
import streamlit as st
import pandas as pd
import altair as alt
from portfolio_optimization import optimize_portfolios


def _fmt_pct(x):
    return 'N/A' if pd.isna(x) else f'{x:.2%}'


def _historical_comparison(returns, benchmark_returns, weights):
    r=returns.apply(pd.to_numeric,errors='coerce').copy()
    w=pd.Series(weights,dtype=float).reindex(r.columns).fillna(0.0)
    portfolio_daily=r.mul(w,axis=1).sum(axis=1,min_count=1)
    benchmark=pd.Series(benchmark_returns,dtype=float).reindex(portfolio_daily.index)
    frame=pd.concat([portfolio_daily.rename('Danh mục'),benchmark.rename('VNINDEX')],axis=1).dropna()
    if frame.empty:return pd.DataFrame()
    return ((1+frame).cumprod()*100).sort_index()


def _allocation_chart(weights):
    chart_data=weights.mul(100).reset_index().rename(columns={'index':'Mã'})
    chart_data=chart_data.melt(id_vars='Mã',var_name='Phương án',value_name='Tỷ trọng')
    return alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('Phương án:N',title='Phương án',axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset('Mã:N',title='Mã cổ phiếu'),
        y=alt.Y('Tỷ trọng:Q',title='Tỷ trọng (%)',scale=alt.Scale(domain=[0,100])),
        color=alt.Color('Mã:N',title='Mã cổ phiếu'),
        tooltip=[alt.Tooltip('Phương án:N'),alt.Tooltip('Mã:N'),alt.Tooltip('Tỷ trọng:Q',format='.2f')]
    ).properties(height=420)


def _render_scenario(label,weights,returns,benchmark_returns,investment_capital,constraints_feasible):
    selected_weights=weights[label].sort_values(ascending=False)
    selected_table=selected_weights[selected_weights>1e-6].rename('Tỷ trọng').to_frame()
    selected_table['Số tiền dự kiến']=selected_table['Tỷ trọng']*float(investment_capital)
    selected_table['Tỷ trọng']=selected_table['Tỷ trọng'].map(lambda x:f'{x:.2%}')
    selected_table['Số tiền dự kiến']=selected_table['Số tiền dự kiến'].map(lambda x:f'{x:,.0f} VNĐ' if x>0 else 'N/A')
    st.markdown(f'**Phương án đang xem: {label}**')
    if not constraints_feasible:
        st.caption('Các tỷ trọng dưới đây chỉ là nghiệm mô hình tham khảo. Chưa đáp ứng giới hạn tỷ trọng trong hồ sơ vì tập cổ phiếu hiện tại chưa đủ rộng.')
    st.dataframe(selected_table,use_container_width=True)
    st.markdown('**Lịch sử phương án so với VNINDEX**')
    historical=_historical_comparison(returns,benchmark_returns,weights[label]) if benchmark_returns is not None else pd.DataFrame()
    if historical.empty:
        st.info('Chưa đủ dữ liệu chung giữa phương án và VNINDEX để vẽ biểu đồ lịch sử.')
    else:
        st.line_chart(historical,use_container_width=True)
        st.caption('Chỉ sử dụng dữ liệu lịch sử. Cả phương án và VNINDEX được quy đổi về 100 tại ngày đầu tiên có dữ liệu chung. Đây là so sánh quá khứ, không phải dự báo lợi nhuận tương lai.')
        st.caption(f"Giai đoạn so sánh: {historical.index.min().strftime('%d/%m/%Y')} đến {historical.index.max().strftime('%d/%m/%Y')}.")


def render_portfolio_optimization(returns,policy,benchmark_returns=None):
    st.header('Bước 7. Tối ưu hóa danh mục')
    st.caption('Xây dựng các phương án phân bổ từ dữ liệu lịch sử. Phân bổ tham chiếu chỉ là mốc so sánh, không phải danh mục nhà đầu tư đang nắm giữ.')
    max_weight=float(policy.get('max_single_stock_weight',0.10)) if policy else 0.10
    target=float(policy.get('target_return',0)) if policy else None
    try:
        result=optimize_portfolios(returns,max_weight=max_weight,target_return=target)
    except Exception as exc:
        st.error(str(exc))
        return

    st.subheader('7.1. So sánh các phương án phân bổ')
    summary=result['summary'].copy()
    summary['Lợi suất kỳ vọng']=summary['Lợi suất kỳ vọng'].map(_fmt_pct)
    summary['Độ biến động']=summary['Độ biến động'].map(_fmt_pct)
    summary['Sharpe Ratio']=summary['Sharpe Ratio'].map(lambda x:'N/A' if pd.isna(x) else f'{x:.2f}')
    st.dataframe(summary,use_container_width=True,hide_index=False)

    constraints_feasible=result.get('constraint_feasible',True)
    if not constraints_feasible:
        required=int(result.get('required_assets',math.ceil(1/result['requested_max_weight'])))
        st.warning(f"Không thể áp dụng đúng giới hạn {result['requested_max_weight']:.0%}/mã với chỉ {result['universe_size']} mã. Cần ít nhất {required} mã để vừa giữ giới hạn này vừa phân bổ đủ 100% vốn cổ phiếu. Các nghiệm ở Bước 7 chỉ để tham khảo, không phải khuyến nghị hợp lệ.")
        st.info('Bạn có thể bổ sung thêm mã cổ phiếu, hoặc nếu tập cổ phiếu hiện tại đã được lựa chọn có chủ đích thì tăng giới hạn tỷ trọng. Hệ thống sẽ tính lại sau khi bạn lưu hồ sơ hoặc lấy dữ liệu mới.')
    elif result.get('target_return') is not None and not result.get('target_feasible',False):
        st.warning('Không tìm thấy phương án thỏa đồng thời mục tiêu lợi nhuận và các ràng buộc hiện tại. Bước 8 sẽ phân tích nguyên nhân và đưa ra hướng xử lý thay vì coi đây là phương án tối ưu.')

    st.subheader('7.2. Phân bổ giữa các phương án')
    weights=result['weights'].copy()
    display=weights.copy()
    for col in display.columns:
        display[col]=display[col].map(lambda x:f'{x:.2%}')
    st.dataframe(display,use_container_width=True)
    st.markdown('**Biểu đồ 7.1. So sánh tỷ trọng giữa các phương án**')
    st.altair_chart(_allocation_chart(weights),use_container_width=True)
    st.caption('Các cột được đặt cạnh nhau theo từng phương án để so sánh trực tiếp tỷ trọng từng mã. Tổng tỷ trọng của mỗi phương án vẫn bằng 100%.')

    scenarios=['Phân bổ tham chiếu','Minimum Variance','Optimal Risky','Maximum Return']
    tabs=st.tabs(scenarios)
    investment_capital=float(st.session_state.get('investment_capital',0))
    for tab,label in zip(tabs,scenarios):
        with tab:
            _render_scenario(label,weights,returns,benchmark_returns,investment_capital,constraints_feasible)

    st.session_state['optimization_result']=result
    st.session_state['scenario_weights']=weights
