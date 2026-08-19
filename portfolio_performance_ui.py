import numpy as np
import pandas as pd
import streamlit as st
from portfolio_risk import calculate_portfolio_risk


def _fmt_pct(x):
    return "N/A" if pd.isna(x) else f"{x:.2%}"


def _fmt_ratio(x):
    return "N/A" if pd.isna(x) or not np.isfinite(x) else f"{x:.2f}"


def render_portfolio_performance(returns, benchmark_returns=None, current_weights=None, risk_free_rate=0.0):
    st.header("Bước 9. Đánh giá hiệu quả lịch sử phương án")
    st.markdown('<div class="section-note">Đánh giá trên dữ liệu quá khứ theo bốn góc nhìn: lợi suất tuyệt đối, hiệu quả điều chỉnh theo tổng rủi ro, hiệu quả so với VNINDEX và mức sụt giảm. Đây là đánh giá lịch sử, không phải dự báo tương lai.</div>', unsafe_allow_html=True)
    if current_weights is not None and len(current_weights) > 0:
        w = pd.Series(current_weights, dtype=float).reindex(returns.columns).fillna(0)
        w = w / w.sum() if w.sum() > 0 else w
        portfolio = returns.mul(w, axis=1).sum(axis=1)
        label = "Phương án đề xuất"
    else:
        portfolio = returns.mean(axis=1)
        label = "Tập cổ phiếu bình quân"

    p = calculate_portfolio_risk(returns, pd.Series(w if current_weights is not None else 1 / len(returns.columns), index=returns.columns), benchmark_returns, risk_free_rate)
    b_weights = pd.Series(1 / len(returns.columns), index=returns.columns)
    b = calculate_portfolio_risk(pd.DataFrame({"VNINDEX": benchmark_returns}), pd.Series({"VNINDEX": 1.0}), None, risk_free_rate) if benchmark_returns is not None else None
    st.session_state["portfolio_performance"] = {
        "Cumulative Return": float((1 + p["portfolio_returns"]).prod() - 1),
        "Annualized Return": p["annual_return"],
        "Annualized Volatility": p["annual_volatility"],
        "Sharpe Ratio": p["sharpe"],
        "Maximum Drawdown": p["max_drawdown"],
    }

    st.subheader("9.1. Kết quả chính")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lợi suất tích lũy", _fmt_pct(st.session_state["portfolio_performance"]["Cumulative Return"]))
    c2.metric("Lợi suất quy đổi theo năm", _fmt_pct(p["annual_return"]))
    c3.metric("Sharpe Ratio", _fmt_ratio(p["sharpe"]))
    c4.metric("Maximum Drawdown", _fmt_pct(p["max_drawdown"]))

    st.subheader("9.2. Đánh giá đa chiều")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sortino Ratio", _fmt_ratio(p["sortino"]))
    c2.metric("Information Ratio", _fmt_ratio(p["information_ratio"]))
    c3.metric("Jensen Alpha", _fmt_pct(p["jensen_alpha"]))
    c4.metric("Tracking Error", _fmt_pct(p["tracking_error"]))
    with st.expander("Chỉ tiêu chuyên sâu", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Beta VNINDEX", _fmt_ratio(p["beta"]))
        c2.metric("Treynor Ratio", _fmt_ratio(p["treynor"]))
        c3.metric("M²", _fmt_pct(p["m2"]))
        c4.metric("R² với VNINDEX", _fmt_pct(p["r_squared"]))
        st.caption("Sharpe đo phần bù lợi suất trên tổng rủi ro. Sortino tập trung vào rủi ro giảm giá. Information Ratio đo lợi suất chủ động trên rủi ro chủ động so với benchmark. Jensen Alpha đo phần lợi suất vượt mức CAPM sau khi điều chỉnh beta. Treynor dùng rủi ro hệ thống. Không một chỉ tiêu nào nên được dùng riêng lẻ.")

    if benchmark_returns is not None:
        st.subheader("9.3. So sánh với VNINDEX")
        active_return = p["active_return"]
        rows = [
            [label, p["annual_return"], p["annual_volatility"], p["sharpe"], p["max_drawdown"]],
            ["VNINDEX", b["annual_return"], b["annual_volatility"], b["sharpe"], b["max_drawdown"]],
        ]
        table = pd.DataFrame(rows, columns=["Đối tượng", "Lợi suất quy đổi theo năm", "Biến động quy đổi theo năm", "Sharpe Ratio", "Maximum Drawdown"])
        for col in ["Lợi suất quy đổi theo năm", "Biến động quy đổi theo năm", "Maximum Drawdown"]:
            table[col] = table[col].map(_fmt_pct)
        table["Sharpe Ratio"] = table["Sharpe Ratio"].map(_fmt_ratio)
        st.dataframe(table, use_container_width=True, hide_index=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Lợi suất chủ động", _fmt_pct(active_return))
        c2.metric("Tracking Error", _fmt_pct(p["tracking_error"]))
        c3.metric("T thống kê lợi suất chủ động", _fmt_ratio(p["active_t_stat"]))
        st.caption("Lợi suất chủ động được tính so với VNINDEX. Information Ratio và t thống kê bổ sung góc nhìn về chất lượng của phần lợi suất vượt benchmark, thay vì chỉ nhìn chênh lệch lợi suất.")

    st.subheader("9.4. Kết luận phương pháp")
    if np.isfinite(p["sharpe"]):
        st.write(f"Sharpe Ratio = {p['sharpe']:.2f}. CFA Institute khuyến nghị dùng Sharpe chủ yếu để so sánh tương đối; không có một ngưỡng tuyệt đối áp dụng cho mọi danh mục.")
    if np.isfinite(p["information_ratio"]):
        st.write(f"Information Ratio = {p['information_ratio']:.2f}. Đây là chỉ tiêu quan trọng khi đánh giá một danh mục chủ động so với benchmark.")
    if np.isfinite(p["jensen_alpha"]):
        st.write(f"Jensen Alpha = {p['jensen_alpha']:.2%}/năm. Giá trị dương cho thấy lợi suất vượt mức giải thích bởi beta thị trường trong mô hình CAPM, nhưng vẫn phụ thuộc vào benchmark và giả định mô hình.")
    st.info("Kết quả lịch sử chịu ảnh hưởng bởi giai đoạn dữ liệu, lựa chọn benchmark, chi phí giao dịch chưa mô phỏng đầy đủ và sai số ước lượng. Không nên kết luận kỹ năng đầu tư chỉ từ một chỉ tiêu hoặc một giai đoạn.")
