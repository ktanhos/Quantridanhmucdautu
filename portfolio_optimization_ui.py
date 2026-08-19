import math
import numpy as np
import streamlit as st
import pandas as pd
import altair as alt
from portfolio_optimization import optimize_portfolios
from portfolio_risk import calculate_portfolio_risk


def _fmt_pct(x):
    return "N/A" if pd.isna(x) else f"{x:.2%}"


def _fmt_ratio(x):
    return "N/A" if pd.isna(x) or not np.isfinite(x) else f"{x:.2f}"


def _fmt_money(x):
    return f"{x:,.0f} VNĐ"


def _inject_ui_style():
    st.markdown("""
    <style>
    .portfolio-subtitle{color:#8f96a3;font-size:.92rem;margin-top:-.35rem;margin-bottom:1.2rem}
    .scenario-card{border:1px solid rgba(128,128,128,.28);border-radius:12px;padding:1rem;min-height:150px;background:rgba(128,128,128,.035)}
    .scenario-card-title{font-size:1rem;font-weight:650;margin-bottom:.65rem}
    .scenario-card-desc{color:#8f96a3;font-size:.78rem;line-height:1.45;min-height:34px}
    .scenario-card-value{font-size:1.35rem;font-weight:650}
    .scenario-card-label{color:#8f96a3;font-size:.72rem}
    .metric-note{color:#8f96a3;font-size:.76rem;line-height:1.45;margin:.15rem 0 .8rem}
    </style>
    """, unsafe_allow_html=True)


def _historical_comparison(returns, benchmark_returns, weights):
    r=returns.apply(pd.to_numeric,errors="coerce").copy()
    w=pd.Series(weights,dtype=float).reindex(r.columns).fillna(0.0)
    portfolio_daily=r.mul(w,axis=1).sum(axis=1,min_count=1)
    benchmark=pd.Series(benchmark_returns,dtype=float).reindex(portfolio_daily.index)
    frame=pd.concat([portfolio_daily.rename("Danh mục"),benchmark.rename("VNINDEX")],axis=1).dropna()
    if frame.empty:return pd.DataFrame()
    return ((1+frame).cumprod()*100).sort_index()


def _allocation_chart(weights):
    """Biểu đồ dùng trực tiếp cùng dữ liệu tỷ trọng với bảng."""
    chart_data=weights.copy().astype(float)
    chart_data.index=chart_data.index.astype(str)
    chart_data.columns=chart_data.columns.astype(str)
    ticker_order=list(chart_data.index)
    scenario_order=list(chart_data.columns)

    chart_data=(
        chart_data.mul(100.0)
        .rename_axis("Mã")
        .reset_index()
        .melt(id_vars="Mã",var_name="Phương án",value_name="Tỷ trọng")
    )
    chart_data["Tỷ trọng"]=pd.to_numeric(chart_data["Tỷ trọng"],errors="coerce")
    chart_data=chart_data.dropna(subset=["Tỷ trọng"])

    sums=chart_data.groupby("Phương án",sort=False)["Tỷ trọng"].sum()
    invalid=sums[~np.isclose(sums.values,100.0,atol=1e-6)]
    if not invalid.empty:
        st.warning("Dữ liệu tỷ trọng của một hoặc nhiều phương án không bằng 100%. Biểu đồ đang hiển thị đúng dữ liệu đầu vào và không tự điều chỉnh tỷ trọng.")

    max_value=float(chart_data["Tỷ trọng"].max()) if not chart_data.empty else 0.0
    chart_max=10 if max_value<=0 else max(10,math.ceil((max_value*1.15)/5)*5)
    chart_max=min(chart_max,100)

    base=alt.Chart(chart_data)

    # Dùng cú pháp tối giản tương thích Altair 6. Không truyền sort vào xOffset
    # vì một số phiên bản Altair 6 không chấp nhận tham số sort ở kênh này.
    bars=base.mark_bar(size=24).encode(
        x=alt.X(
            "Phương án:N",
            title="Phương án",
            sort=scenario_order,
            axis=alt.Axis(labelAngle=0,labelLimit=160,titlePadding=14),
        ),
        xOffset=alt.XOffset("Mã:N"),
        y=alt.Y(
            "Tỷ trọng:Q",
            title="Tỷ trọng (%)",
            scale=alt.Scale(domain=[0,chart_max],nice=False),
            axis=alt.Axis(format=".0f",tickCount=max(3,int(chart_max/5)+1),titlePadding=10),
        ),
        color=alt.Color(
            "Mã:N",
            title="Mã cổ phiếu",
            legend=alt.Legend(orient="right",symbolType="square"),
        ),
        tooltip=[
            alt.Tooltip("Phương án:N",title="Phương án"),
            alt.Tooltip("Mã:N",title="Mã cổ phiếu"),
            alt.Tooltip("Tỷ trọng:Q",title="Tỷ trọng",format=".2f"),
        ],
    )

    labels=base.mark_text(dy=-8,fontSize=10).encode(
        x=alt.X("Phương án:N",sort=scenario_order),
        xOffset=alt.XOffset("Mã:N"),
        y=alt.Y("Tỷ trọng:Q",scale=alt.Scale(domain=[0,chart_max],nice=False)),
        text=alt.Text("Tỷ trọng:Q",format=".1f"),
    )

    return (bars+labels).properties(height=390)


def _scenario_metrics(result,label,benchmark_returns):
    return calculate_portfolio_risk(result["returns"],result["weights"][label],benchmark_returns=benchmark_returns)


def _scenario_metrics_table(result,weights,benchmark_returns):
    rows=[]
    for label in weights.columns:
        m=_scenario_metrics(result,label,benchmark_returns)
        rows.append({"Phương án":label,"Lợi suất lịch sử":m["annual_return"],"Biến động":m["annual_volatility"],"Sharpe":m["sharpe"],"Sortino":m["sortino"],"Maximum Drawdown":m["max_drawdown"],"VaR 95% ngày":m["var_95_daily"],"CVaR 95% ngày":m["cvar_95_daily"],"Beta VNINDEX":m["beta"],"Information Ratio":m["information_ratio"],"HHI":m["concentration_hhi"]})
    table=pd.DataFrame(rows).set_index("Phương án")
    for col in ["Lợi suất lịch sử","Biến động","Maximum Drawdown","VaR 95% ngày","CVaR 95% ngày"]:table[col]=table[col].map(_fmt_pct)
    for col in ["Sharpe","Sortino","Beta VNINDEX","Information Ratio"]:table[col]=table[col].map(_fmt_ratio)
    table["HHI"]=table["HHI"].map(lambda x:"N/A" if pd.isna(x) else f"{x:.3f}")
    return table


def _scenario_cards(result,weights,benchmark_returns):
    descriptions={"Phân bổ tham chiếu":"Mốc so sánh, chia đều vốn cho các mã.","Minimum Variance":"Ưu tiên giảm mức biến động của danh mục.","Optimal Risky":"Tìm sự cân bằng giữa lợi suất và rủi ro.","Maximum Return":"Ưu tiên lợi suất ước tính trong giới hạn tỷ trọng."}
    cols=st.columns(len(weights.columns))
    for col,label in zip(cols,weights.columns):
        m=_scenario_metrics(result,label,benchmark_returns)
        with col:
            st.markdown(f'<div class="scenario-card"><div class="scenario-card-title">{label}</div><div class="scenario-card-desc">{descriptions.get(label,"Phương án phân bổ vốn.")}</div><div class="scenario-card-label">Lợi suất lịch sử</div><div class="scenario-card-value">{_fmt_pct(m["annual_return"])}</div><div style="margin-top:.45rem">Sharpe <b>{_fmt_ratio(m["sharpe"])}</b> · Drawdown <b>{_fmt_pct(m["max_drawdown"])}</b></div></div>',unsafe_allow_html=True)


def _scenario_detail(label,result,weights,benchmark_returns,investment_capital):
    m=_scenario_metrics(result,label,benchmark_returns)
    st.markdown(f"### {label}")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Lợi suất lịch sử",_fmt_pct(m["annual_return"]));c2.metric("Biến động",_fmt_pct(m["annual_volatility"]));c3.metric("Sharpe Ratio",_fmt_ratio(m["sharpe"]));c4.metric("Sortino Ratio",_fmt_ratio(m["sortino"]))
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Maximum Drawdown",_fmt_pct(m["max_drawdown"]));c2.metric("VaR 95% ngày",_fmt_pct(m["var_95_daily"]));c3.metric("CVaR 95% ngày",_fmt_pct(m["cvar_95_daily"]));c4.metric("Calmar Ratio",_fmt_ratio(m["calmar"]))
    with st.expander("Chỉ tiêu chuyên sâu",expanded=False):
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Beta VNINDEX",_fmt_ratio(m["beta"]));c2.metric("Information Ratio",_fmt_ratio(m["information_ratio"]));c3.metric("HHI",f"{m['concentration_hhi']:.3f}");c4.metric("Số vị thế tương đương",f"{m['effective_positions']:.1f}")
        st.markdown('<div class="metric-note">HHI đo mức độ tập trung. Chỉ số càng cao thì danh mục càng phụ thuộc vào ít mã. Số vị thế tương đương giúp diễn giải mức độ đa dạng hóa dễ hiểu hơn.</div>',unsafe_allow_html=True)
    with st.expander("Phân bổ vốn",expanded=True):
        selected=weights[label].sort_values(ascending=False)
        table=selected[selected>1e-6].rename("Tỷ trọng").to_frame()
        table["Số tiền dự kiến"]=table["Tỷ trọng"]*float(investment_capital)
        table["Tỷ trọng"]=table["Tỷ trọng"].map(lambda x:f"{x:.2%}")
        table["Số tiền dự kiến"]=table["Số tiền dự kiến"].map(_fmt_money)
        st.dataframe(table,use_container_width=True)
    st.markdown("#### Lịch sử phương án so với VNINDEX")
    historical=_historical_comparison(result["returns"],benchmark_returns,weights[label]) if benchmark_returns is not None else pd.DataFrame()
    if historical.empty:st.info("Chưa đủ dữ liệu chung giữa phương án và VNINDEX để vẽ biểu đồ lịch sử.")
    else:
        st.line_chart(historical,use_container_width=True)
        st.caption("Danh mục và VNINDEX được quy đổi về 100 tại ngày đầu tiên có dữ liệu chung. Đây chỉ là so sánh quá khứ, không phải dự báo lợi nhuận tương lai.")
        st.caption(f"Giai đoạn: {historical.index.min().strftime('%d/%m/%Y')} đến {historical.index.max().strftime('%d/%m/%Y')}.")


def render_portfolio_optimization(returns,policy,benchmark_returns=None):
    _inject_ui_style()
    st.header("Bước 7. Tối ưu hóa danh mục")
    st.markdown('<div class="portfolio-subtitle">Hệ thống xây dựng nhiều phương án phân bổ từ dữ liệu lịch sử, sau đó so sánh lợi suất, rủi ro và mức độ phù hợp. Phân bổ tham chiếu chỉ là mốc so sánh.</div>',unsafe_allow_html=True)
    max_weight=float(policy.get("max_single_stock_weight",0.10)) if policy else 0.10
    target=float(policy.get("target_return",0)) if policy else None
    try:result=optimize_portfolios(returns,max_weight=max_weight,target_return=target)
    except Exception as exc:st.error(str(exc));return
    weights=result["weights"].copy();n=len(weights.index)
    if abs(result["requested_max_weight"]-1/n)<1e-10:
        st.info(f"Tập hiện tại có {n} mã và giới hạn {result['requested_max_weight']:.0%}/mã. Ràng buộc này khiến mọi mã phải nhận đúng tỷ trọng giới hạn, vì vậy các phương án có thể trùng nhau. Muốn mô hình có thêm không gian tối ưu, hãy mở rộng tập mã hoặc điều chỉnh giới hạn.")
    if result.get("target_return") is not None and not result.get("target_feasible",False):st.warning("Chưa có phương án thỏa đồng thời mục tiêu lợi nhuận và các giới hạn hiện tại. Không nên coi một nghiệm không đạt mục tiêu là danh mục tối ưu.")

    st.subheader("7.1. Nhìn nhanh các phương án")
    _scenario_cards(result,weights,benchmark_returns)
    st.markdown('<div class="metric-note">Lợi suất lịch sử và các chỉ tiêu rủi ro được tính lại trên chuỗi dữ liệu quá khứ của từng phương án.</div>',unsafe_allow_html=True)

    st.subheader("7.2. So sánh hiệu quả và rủi ro")
    st.dataframe(_scenario_metrics_table(result,weights,benchmark_returns),use_container_width=True,hide_index=False)

    st.subheader("7.3. So sánh tỷ trọng")
    display=weights.copy()
    for col in display.columns:display[col]=display[col].map(lambda x:f"{x:.2%}")
    st.dataframe(display,use_container_width=True)
    st.markdown("**Biểu đồ 7.1. So sánh tỷ trọng giữa các phương án**")
    st.altair_chart(_allocation_chart(weights),use_container_width=True)
    st.caption("Biểu đồ sử dụng trực tiếp cùng bộ tỷ trọng với bảng phía trên. Số trên mỗi cột là tỷ trọng thực tế; tổng mỗi phương án được kiểm tra bằng 100%.")

    st.subheader("7.4. Xem chi tiết từng phương án")
    st.caption("Chọn một phương án để xem phân bổ vốn, các chỉ tiêu chuyên sâu và lịch sử so với VNINDEX.")
    scenarios=["Phân bổ tham chiếu","Minimum Variance","Optimal Risky","Maximum Return"]
    tabs=st.tabs(scenarios);investment_capital=float(st.session_state.get("investment_capital",0))
    for tab,label in zip(tabs,scenarios):
        with tab:_scenario_detail(label,result,weights,benchmark_returns,investment_capital)
    st.session_state["optimization_result"]=result
    st.session_state["scenario_weights"]=weights
