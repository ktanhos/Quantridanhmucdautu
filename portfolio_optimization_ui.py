import math
import numpy as np
import streamlit as st
import pandas as pd
import altair as alt
from portfolio_optimization import optimize_portfolios
from portfolio_risk import calculate_portfolio_risk

def _fmt_pct(x): return "N/A" if pd.isna(x) else f"{x:.2%}"
def _fmt_ratio(x): return "N/A" if pd.isna(x) or not np.isfinite(x) else f"{x:.2f}"
def _fmt_money(x): return f"{x:,.0f} VNĐ"

def _inject_ui_style():
    st.markdown("""<style>.portfolio-subtitle{color:#8f96a3;font-size:.92rem;margin-top:-.35rem;margin-bottom:1.2rem}.scenario-card{border:1px solid rgba(128,128,128,.28);border-radius:12px;padding:1rem;min-height:150px;background:rgba(128,128,128,.035)}.scenario-card-title{font-size:1rem;font-weight:650;margin-bottom:.65rem}.scenario-card-desc{color:#8f96a3;font-size:.78rem;line-height:1.45;min-height:34px}.scenario-card-value{font-size:1.35rem;font-weight:650}.scenario-card-label,.metric-note{color:#8f96a3;font-size:.76rem;line-height:1.45}</style>""",unsafe_allow_html=True)

def _historical_comparison(returns,benchmark_returns,weights):
    r=returns.apply(pd.to_numeric,errors="coerce").copy();w=pd.Series(weights,dtype=float).reindex(r.columns).fillna(0.0);daily=r.dropna(how="any").mul(w,axis=1).sum(axis=1);benchmark=pd.Series(benchmark_returns,dtype=float).reindex(daily.index);frame=pd.concat([daily.rename("Danh mục"),benchmark.rename("VNINDEX")],axis=1).dropna();return pd.DataFrame() if frame.empty else ((1+frame).cumprod()*100).sort_index()

def _allocation_chart(weights):
    d=weights.copy().astype(float);d.index=d.index.astype(str);d.columns=d.columns.astype(str);order=list(d.columns);d=d.mul(100).rename_axis("Mã").reset_index().melt(id_vars="Mã",var_name="Phương án",value_name="Tỷ trọng");d=d.dropna(subset=["Tỷ trọng"]);mx=float(d["Tỷ trọng"].max()) if not d.empty else 0;top=min(max(10,math.ceil(mx*1.15/5)*5),100);base=alt.Chart(d);bars=base.mark_bar(size=24).encode(x=alt.X("Phương án:N",sort=order),xOffset=alt.XOffset("Mã:N"),y=alt.Y("Tỷ trọng:Q",title="Tỷ trọng %",scale=alt.Scale(domain=[0,top],nice=False)),color=alt.Color("Mã:N",title="Mã cổ phiếu"),tooltip=["Phương án:N","Mã:N",alt.Tooltip("Tỷ trọng:Q",format=".2f")]);labels=base.mark_text(dy=-8,fontSize=10).encode(x=alt.X("Phương án:N",sort=order),xOffset=alt.XOffset("Mã:N"),y=alt.Y("Tỷ trọng:Q",scale=alt.Scale(domain=[0,top],nice=False)),text=alt.Text("Tỷ trọng:Q",format=".1f"));return (bars+labels).properties(height=390)

def _scenario_metrics(result,label,benchmark_returns): return calculate_portfolio_risk(result["returns"],result["weights"][label],benchmark_returns=benchmark_returns,risk_free_rate=float(result.get("risk_free_rate",0.04)))
def _scenario_metrics_table(result,weights,benchmark_returns):
    rows=[]
    for label in weights.columns:
        m=_scenario_metrics(result,label,benchmark_returns);rows.append({"Phương án":label,"Lợi suất lịch sử":m["annual_return"],"Biến động":m["annual_volatility"],"Sharpe":m["sharpe"],"Sortino":m["sortino"],"Maximum Drawdown":m["max_drawdown"],"Information Ratio":m["information_ratio"]})
    t=pd.DataFrame(rows).set_index("Phương án")
    for c in ["Lợi suất lịch sử","Biến động","Maximum Drawdown"]:t[c]=t[c].map(_fmt_pct)
    for c in ["Sharpe","Sortino","Information Ratio"]:t[c]=t[c].map(_fmt_ratio)
    return t

def _scenario_cards(result,weights,benchmark_returns):
    descriptions={"Phân bổ tham chiếu":"Mốc so sánh, chia đều vốn cho các mã.","Minimum Variance":"Ưu tiên làm danh mục ổn định hơn.","Optimal Risky":"Tìm sự cân bằng giữa lợi nhuận và mức lên xuống.","Maximum Return":"Ưu tiên lợi suất ước tính trong giới hạn tỷ trọng."};cols=st.columns(len(weights.columns))
    for col,label in zip(cols,weights.columns):
        m=_scenario_metrics(result,label,benchmark_returns)
        with col:st.markdown(f'<div class="scenario-card"><div class="scenario-card-title">{label}</div><div class="scenario-card-desc">{descriptions.get(label,"Phương án phân bổ vốn.")}</div><div class="scenario-card-label">Lợi suất lịch sử</div><div class="scenario-card-value">{_fmt_pct(m["annual_return"])}</div><div style="margin-top:.45rem">Sharpe <b>{_fmt_ratio(m["sharpe"])}</b> · Giảm mạnh nhất <b>{_fmt_pct(m["max_drawdown"])}</b></div></div>',unsafe_allow_html=True)

def _scenario_detail(label,result,weights,benchmark_returns,investment_capital):
    m=_scenario_metrics(result,label,benchmark_returns);st.markdown(f"### {label}");c1,c2,c3,c4=st.columns(4);c1.metric("Lợi suất lịch sử",_fmt_pct(m["annual_return"]));c2.metric("Biến động",_fmt_pct(m["annual_volatility"]));c3.metric("Sharpe Ratio",_fmt_ratio(m["sharpe"]));c4.metric("Sortino Ratio",_fmt_ratio(m["sortino"]))
    with st.expander("Xem thêm các chỉ tiêu",expanded=False):
        c1,c2,c3,c4=st.columns(4);c1.metric("Beta VNINDEX",_fmt_ratio(m["beta"]));c2.metric("Information Ratio",_fmt_ratio(m["information_ratio"]));c3.metric("Jensen Alpha",_fmt_pct(m["jensen_alpha"]));c4.metric("Treynor Ratio",_fmt_ratio(m["treynor"]));st.write("Các chỉ tiêu này giúp nhìn danh mục từ nhiều góc độ. Information Ratio xem phần kết quả tốt hơn hoặc kém hơn VNINDEX có tương xứng với mức khác biệt so với VNINDEX hay không. Jensen Alpha ước tính phần lợi nhuận còn lại sau khi đã tính đến mức danh mục thường đi cùng thị trường. Treynor xem lợi nhuận so với phần rủi ro đến từ biến động chung của thị trường.")
    with st.expander("Tỷ trọng từng cổ phiếu",expanded=True):
        table=weights[label].sort_values(ascending=False);table=table[table>1e-6].rename("Tỷ trọng").to_frame();table["Số tiền dự kiến"]=table["Tỷ trọng"]*float(investment_capital);table["Tỷ trọng"]=table["Tỷ trọng"].map(lambda x:f"{x:.2%}");table["Số tiền dự kiến"]=table["Số tiền dự kiến"].map(_fmt_money);st.dataframe(table,use_container_width=True)

def render_portfolio_optimization(returns,policy,benchmark_returns=None):
    _inject_ui_style();st.header("Bước 5. Chia tỷ trọng cho từng cổ phiếu");st.markdown('<div class="portfolio-subtitle">Hệ thống thử nhiều cách chia tiền giữa các mã, sau đó so sánh để xem phương án nào phù hợp hơn với mục tiêu và mức rủi ro của bạn. Phân bổ tham chiếu chỉ là mốc so sánh.</div>',unsafe_allow_html=True)
    max_weight=float(policy.get("max_single_stock_weight",0.10)) if policy else 0.10;target=float(policy.get("target_return",0)) if policy else None;rf=float(policy.get("risk_free_rate",0.04)) if policy else 0.04
    try:result=optimize_portfolios(returns,max_weight=max_weight,risk_free_rate=rf,target_return=target)
    except Exception as exc:st.error(str(exc));return
    weights=result["weights"].copy();n=len(weights.index)
    if abs(result["requested_max_weight"]-1/n)<1e-10:st.info(f"Tập hiện tại có {n} mã và giới hạn {result['requested_max_weight']:.0%} mỗi mã. Với giới hạn này, một số phương án có thể gần giống nhau.")
    if result.get("target_return") is not None and not result.get("target_feasible",False):st.warning("Chưa có phương án vừa đạt mục tiêu lợi nhuận vừa thỏa các giới hạn hiện tại. Có thể cần xem lại mục tiêu hoặc tập cổ phiếu.")
    st.subheader("5.1. Nhìn nhanh các phương án");_scenario_cards(result,weights,benchmark_returns);st.subheader("5.2. So sánh hiệu quả và rủi ro");st.dataframe(_scenario_metrics_table(result,weights,benchmark_returns),use_container_width=True)
    st.subheader("5.3. So sánh tỷ trọng");display=weights.copy()
    for col in display.columns:display[col]=display[col].map(lambda x:f"{x:.2%}")
    st.dataframe(display,use_container_width=True);st.altair_chart(_allocation_chart(weights),use_container_width=True)
    st.subheader("5.4. Xem chi tiết từng phương án");tabs=st.tabs(list(weights.columns));capital=float(st.session_state.get("investment_capital",0))
    for tab,label in zip(tabs,weights.columns):
        with tab:_scenario_detail(label,result,weights,benchmark_returns,capital)
    st.session_state["optimization_result"]=result;st.session_state["scenario_weights"]=weights
