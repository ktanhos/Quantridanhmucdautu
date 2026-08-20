import numpy as np
import pandas as pd
import streamlit as st
from portfolio_risk import calculate_portfolio_risk


def _fmt(x, kind="ratio"):
    if pd.isna(x) or not np.isfinite(x):
        return "N/A"
    return f"{x:.2%}" if kind == "pct" else f"{x:.2f}"


def render_portfolio_risk(returns, benchmark_returns, risk_free_rate=0.0):
    st.header("Bước 6. Phân tích rủi ro tập cổ phiếu")
    st.markdown('<div class="section-note">Phân tích tập cổ phiếu trên cùng một cơ sở dữ liệu trước khi tối ưu hóa. Tỷ trọng chia đều chỉ là mốc tham chiếu, không phải danh mục người dùng phải mua.</div>', unsafe_allow_html=True)
    tickers = list(returns.columns)
    if len(tickers) < 2:
        st.warning("Cần ít nhất 2 mã cổ phiếu để thực hiện phân tích đa dạng hóa.")
        return
    equal_weight = 1 / len(tickers)
    weights = pd.Series(equal_weight, index=tickers, dtype=float)
    try:
        result = calculate_portfolio_risk(returns, weights, benchmark_returns, risk_free_rate)
    except Exception as exc:
        st.error(str(exc))
        return

    st.subheader("6.1. Bức tranh rủi ro chính")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lợi suất quy đổi theo năm", _fmt(result["annual_return"], "pct"))
    c2.metric("Biến động quy đổi theo năm", _fmt(result["annual_volatility"], "pct"))
    c3.metric("Sharpe Ratio", _fmt(result["sharpe"]))
    c4.metric("Maximum Drawdown", _fmt(result["max_drawdown"], "pct"))

    st.subheader("6.2. Đánh giá điều chỉnh theo rủi ro")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sortino Ratio", _fmt(result["sortino"]))
    c2.metric("Information Ratio", _fmt(result["information_ratio"]))
    c3.metric("Jensen Alpha", _fmt(result["jensen_alpha"], "pct"))
    c4.metric("Tracking Error", _fmt(result["tracking_error"], "pct"))
    st.caption("Sharpe cho biết lợi suất vượt lãi suất phi rủi ro so với mức biến động. Information Ratio phù hợp khi xem phần lợi suất vượt VNINDEX. Sortino tập trung hơn vào rủi ro giảm giá. Jensen Alpha cho biết phần lợi suất vượt mức giải thích bởi beta thị trường trong mô hình CAPM.")

    with st.expander("Chỉ tiêu chuyên sâu", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Beta VNINDEX", _fmt(result["beta"]))
        c2.metric("Treynor Ratio", _fmt(result["treynor"]))
        c3.metric("R² với VNINDEX", _fmt(result["r_squared"]))
        c4.metric("T thống kê lợi suất chủ động", _fmt(result["active_t_stat"]))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("VaR 95% theo ngày", _fmt(result["var_95_daily"], "pct"))
        c2.metric("CVaR 95% theo ngày", _fmt(result["cvar_95_daily"], "pct"))
        c3.metric("HHI", f"{result['concentration_hhi']:.3f}")
        c4.metric("Số vị thế tương đương", f"{result['effective_positions']:.1f}")

    st.subheader("6.3. Đóng góp rủi ro")
    rc = result["risk_contribution"].sort_values(ascending=False).rename("Đóng góp rủi ro")
    table = rc.to_frame()
    table["Tỷ trọng tham chiếu"] = result["weights"]
    table["Đóng góp rủi ro"] = table["Đóng góp rủi ro"].map(lambda x: f"{x:.2%}")
    table["Tỷ trọng tham chiếu"] = table["Tỷ trọng tham chiếu"].map(lambda x: f"{x:.2%}")
    st.dataframe(table, use_container_width=True, hide_index=False)

    with st.expander("Tương quan giữa các cổ phiếu", expanded=False):
        st.dataframe(result["correlation"].round(3), use_container_width=True)
        st.caption("Tương quan thấp có thể hỗ trợ đa dạng hóa nhưng không bảo đảm giảm rủi ro trong mọi giai đoạn.")

    with st.expander("Diễn giải Sharpe", expanded=True):
        if np.isfinite(result["sharpe"]):
            st.write(f"Sharpe Ratio hiện tại là {result['sharpe']:.2f}. Chỉ tiêu này cho biết danh mục tạo ra bao nhiêu lợi suất vượt lãi suất phi rủi ro trên mỗi đơn vị biến động. Sharpe càng cao thì hiệu quả trên rủi ro càng tốt, nhưng không nên đánh giá danh mục chỉ bằng một ngưỡng cố định. Nên so sánh với các phương án khác, VNINDEX và mức rủi ro mà bạn chấp nhận.")
        st.write(f"Lãi suất phi rủi ro đang dùng: {risk_free_rate:.2%}/năm.")
        st.write("Sharpe chỉ nhìn rủi ro tổng thể. Nên xem thêm Sortino để biết rủi ro giảm giá, Maximum Drawdown để biết danh mục từng giảm sâu đến đâu và CVaR để xem mức thua lỗ trong những ngày xấu nhất.")
