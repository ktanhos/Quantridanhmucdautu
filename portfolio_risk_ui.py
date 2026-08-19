import numpy as np
import pandas as pd
import streamlit as st
from portfolio_risk import calculate_portfolio_risk


def render_portfolio_risk(returns, benchmark_returns):
    st.header("Bước 6. Phân tích rủi ro tập cổ phiếu")
    st.caption("Phân tích mức lợi suất, biến động, tương quan và rủi ro của tập cổ phiếu trước khi hệ thống xây dựng các phương án phân bổ. Người dùng không cần nhập tỷ trọng hiện tại.")

    tickers = list(returns.columns)
    if len(tickers) < 2:
        st.warning("Cần ít nhất 2 mã cổ phiếu để thực hiện phân tích đa dạng hóa.")
        return

    equal_weight = 1 / len(tickers)
    weights = pd.Series(equal_weight, index=tickers, dtype=float)

    st.subheader("6.1. Phân tích cơ sở")
    c1, c2, c3 = st.columns(3)
    c1.metric("Số cổ phiếu được phân tích", f"{len(tickers):,}")
    c2.metric("Tỷ trọng tham chiếu mỗi mã", f"{equal_weight:.2%}")
    c3.metric("Tổng tỷ trọng tham chiếu", f"{weights.sum():.2%}")
    st.info("Tỷ trọng tham chiếu chia đều vốn cho các mã chỉ để tạo một mốc so sánh. Nó không có nghĩa là bạn phải mua mỗi mã bằng nhau và không phải danh mục tối ưu.")

    try:
        result = calculate_portfolio_risk(returns, weights, benchmark_returns)
    except Exception as exc:
        st.error(str(exc))
        return

    st.subheader("6.2. Tổng quan rủi ro và lợi suất")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lợi suất năm hóa", f"{result['annual_return']:.2%}")
    c2.metric("Biến động năm hóa", f"{result['annual_volatility']:.2%}")
    c3.metric("Sharpe Ratio", f"{result['sharpe']:.2f}")
    c4.metric("Sortino Ratio", f"{result['sortino']:.2f}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Maximum Drawdown", f"{result['max_drawdown']:.2%}")
    c2.metric("Calmar Ratio", f"{result['calmar']:.2f}" if np.isfinite(result['calmar']) else "N/A")
    c3.metric("VaR 95% theo ngày", f"{result['var_95_daily']:.2%}")
    c4.metric("CVaR 95% theo ngày", f"{result['cvar_95_daily']:.2%}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Beta với VNINDEX", f"{result['beta']:.2f}" if np.isfinite(result['beta']) else "N/A")
    c2.metric("Information Ratio", f"{result['information_ratio']:.2f}" if np.isfinite(result['information_ratio']) else "N/A")
    c3.metric("HHI", f"{result['concentration_hhi']:.3f}")
    c4.metric("Số vị thế tương đương", f"{result['effective_positions']:.1f}")

    st.markdown("**Bảng 6.1. Đóng góp rủi ro theo cổ phiếu**")
    rc = result["risk_contribution"].sort_values(ascending=False).rename("Đóng góp rủi ro")
    table = rc.to_frame()
    table["Tỷ trọng tham chiếu"] = result["weights"]
    table["Đóng góp rủi ro"] = table["Đóng góp rủi ro"].map(lambda x: f"{x:.2%}")
    table["Tỷ trọng tham chiếu"] = table["Tỷ trọng tham chiếu"].map(lambda x: f"{x:.2%}")
    st.dataframe(table, use_container_width=True)

    st.markdown("**Bảng 6.2. Tương quan giữa các cổ phiếu**")
    st.dataframe(result["correlation"].round(3), use_container_width=True)
    st.caption("Tương quan gần 1 nghĩa là hai mã thường biến động cùng chiều; gần 0 là ít liên hệ tuyến tính; gần âm 1 là thường biến động ngược chiều. Tương quan thấp có thể giúp đa dạng hóa tốt hơn, nhưng không bảo đảm giảm rủi ro trong mọi giai đoạn.")

    st.markdown("**Bảng 6.3. Mức độ tập trung của phân bổ tham chiếu**")
    hhi = float(result["concentration_hhi"])
    effective_positions = float(result["effective_positions"])
    c1, c2 = st.columns(2)
    c1.metric("Chỉ số tập trung HHI", f"{hhi:.3f}")
    c2.metric("Số vị thế tương đương", f"{effective_positions:.1f}")
    st.caption("HHI là chỉ số đo mức độ tập trung của tỷ trọng. HHI được tính bằng tổng bình phương các tỷ trọng. HHI càng cao thì tiền càng tập trung vào ít mã. Số vị thế tương đương = 1/HHI giúp diễn giải trực quan hơn. HHI không nói cổ phiếu có rủi ro cao hay thấp và cũng không xét tương quan giữa các mã.")

    st.subheader("6.3. Diễn giải nhanh")
    sharpe = result["sharpe"]
    vol = result["annual_volatility"]
    if np.isfinite(sharpe):
        if sharpe >= 1:
            sharpe_text = "Hiệu quả điều chỉnh theo rủi ro của phân bổ tham chiếu đang ở mức tốt."
        elif sharpe >= 0.5:
            sharpe_text = "Hiệu quả điều chỉnh theo rủi ro của phân bổ tham chiếu ở mức khá."
        else:
            sharpe_text = "Hiệu quả điều chỉnh theo rủi ro của phân bổ tham chiếu còn thấp."
        st.write(f"Sharpe Ratio {sharpe:.2f}: {sharpe_text}")
    st.write(f"Biến động năm hóa {vol:.2%}: đây là mức biến động ước tính của phân bổ đều trong giai đoạn dữ liệu được phân tích.")
    st.write("Các kết quả ở bước này chỉ mô tả đặc điểm rủi ro của tập cổ phiếu. Bước tối ưu hóa tiếp theo mới quyết định tỷ trọng và phương án phù hợp với hồ sơ nhà đầu tư.")
