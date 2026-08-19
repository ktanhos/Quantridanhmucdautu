import numpy as np
import pandas as pd
import streamlit as st


def _stats(r):
    r = pd.Series(r, dtype=float).dropna()
    if r.empty:
        return {"Cumulative Return": np.nan, "Annualized Return": np.nan, "Annualized Volatility": np.nan, "Sharpe Ratio": np.nan, "Maximum Drawdown": np.nan}
    wealth = (1 + r).cumprod()
    years = len(r) / 252
    ann = wealth.iloc[-1] ** (1 / years) - 1 if years > 0 else np.nan
    vol = r.std(ddof=1) * np.sqrt(252)
    sh = ann / vol if vol > 0 else np.nan
    dd = (wealth / wealth.cummax() - 1).min()
    return {"Cumulative Return": wealth.iloc[-1] - 1, "Annualized Return": ann, "Annualized Volatility": vol, "Sharpe Ratio": sh, "Maximum Drawdown": dd}


def _fmt_pct(x):
    return "N/A" if pd.isna(x) else f"{x:.2%}"


def _fmt_ratio(x):
    return "N/A" if pd.isna(x) else f"{x:.2f}"


def render_portfolio_performance(returns, benchmark_returns=None, current_weights=None):
    st.header("Bước 9. Kiểm tra hiệu quả lịch sử phương án")
    st.markdown('<div class="section-note">Đặt phương án đề xuất cạnh VNINDEX trên cùng giai đoạn dữ liệu. Đây là kiểm tra quá khứ để hỗ trợ đánh giá, không phải dự báo tương lai.</div>', unsafe_allow_html=True)
    if current_weights is not None and len(current_weights) > 0:
        w = pd.Series(current_weights, dtype=float).reindex(returns.columns).fillna(0)
        w = w / w.sum() if w.sum() > 0 else w
        portfolio = returns.mul(w, axis=1).sum(axis=1)
        label = "Phương án đề xuất"
    else:
        portfolio = returns.mean(axis=1)
        label = "Tập cổ phiếu bình quân"
    p = _stats(portfolio)
    b = _stats(benchmark_returns) if benchmark_returns is not None else None
    st.session_state["portfolio_performance"] = p

    st.subheader("9.1. Kết quả chính")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lợi suất tích lũy", _fmt_pct(p["Cumulative Return"]))
    c2.metric("Lợi suất quy đổi theo năm", _fmt_pct(p["Annualized Return"]))
    c3.metric("Sharpe Ratio", _fmt_ratio(p["Sharpe Ratio"]))
    c4.metric("Maximum Drawdown", _fmt_pct(p["Maximum Drawdown"]))

    if b:
        spread = p["Annualized Return"] - b["Annualized Return"] if pd.notna(p["Annualized Return"]) and pd.notna(b["Annualized Return"]) else np.nan
        c1, c2, c3 = st.columns(3)
        c1.metric("Lợi suất phương án", _fmt_pct(p["Annualized Return"]))
        c2.metric("Lợi suất VNINDEX", _fmt_pct(b["Annualized Return"]))
        c3.metric("Chênh lệch so với VNINDEX", _fmt_pct(spread), delta=None)

    rows = [[label, p["Cumulative Return"], p["Annualized Return"], p["Annualized Volatility"], p["Sharpe Ratio"], p["Maximum Drawdown"]]]
    if b:
        rows.append(["VNINDEX", b["Cumulative Return"], b["Annualized Return"], b["Annualized Volatility"], b["Sharpe Ratio"], b["Maximum Drawdown"]])
    table = pd.DataFrame(rows, columns=["Đối tượng", "Lợi suất tích lũy", "Lợi suất quy đổi theo năm", "Biến động quy đổi theo năm", "Sharpe Ratio", "Maximum Drawdown"])
    for col in ["Lợi suất tích lũy", "Lợi suất quy đổi theo năm", "Biến động quy đổi theo năm", "Maximum Drawdown"]:
        table[col] = table[col].map(_fmt_pct)
    table["Sharpe Ratio"] = table["Sharpe Ratio"].map(_fmt_ratio)

    st.subheader("9.2. So sánh với VNINDEX")
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.info("Danh mục và VNINDEX được so sánh trên dữ liệu quá khứ đã chọn. Kết quả lịch sử không bảo đảm kết quả tương lai.")
