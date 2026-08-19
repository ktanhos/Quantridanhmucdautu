from __future__ import annotations
import pandas as pd
import streamlit as st
from market_regime import calculate_market_regime


def render_market_regime(index_prices: pd.Series, stock_prices: pd.DataFrame | None = None) -> None:
    st.header("Bước 5. Đánh giá Market Regime")
    st.caption("Hệ thống đánh giá trạng thái thị trường từ xu hướng, độ rộng, động lượng, biến động và thanh khoản. Mọi kết luận đều có thể truy ngược về số liệu bên dưới.")
    try:
        result = calculate_market_regime(index_prices, stock_prices)
    except ValueError as exc:
        st.warning(str(exc))
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Market Score", f"{result.score:.1f} / 100")
    c2.metric("Market Regime", result.regime)
    c3.metric("Độ tin cậy", result.confidence)
    c4.metric("Tỷ trọng cổ phiếu tham chiếu", f"{result.equity_min:.0%} đến {result.equity_max:.0%}")

    st.markdown("**Bảng 5.1. Điểm Market Regime và mức đóng góp**")
    display = result.components.copy()
    display["Điểm"] = display["Điểm"].round(1)
    display["Trọng số"] = display["Trọng số"].map(lambda x: f"{x:.0%}")
    display["Đóng góp"] = display["Đóng góp"].round(1)
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("**Bảng 5.2. Các chỉ báo xác định trạng thái thị trường**")
    rows = []
    for name, value in result.indicators.items():
        if name.startswith("%"):
            text = "N/A" if pd.isna(value) else f"{value:.1f}%"
        elif "Return" in name or "Drawdown" in name or "change" in name:
            text = "N/A" if pd.isna(value) else f"{value:.2%}"
        elif "Volatility" in name:
            text = "N/A" if pd.isna(value) else f"{value:.2%}"
        elif "/" in name:
            text = "N/A" if pd.isna(value) else f"{value:.3f}"
        elif name == "Stocks analyzed":
            text = str(int(value))
        else:
            text = "N/A" if pd.isna(value) else f"{value:.3f}"
        rows.append({"Chỉ báo": name, "Giá trị": text})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("**Bảng 5.3. Ngưỡng phân loại Market Regime**")
    st.dataframe(pd.DataFrame([
        ["80 đến 100", "Tích cực mạnh", "90% đến 100%"],
        ["65 đến dưới 80", "Tích cực", "70% đến 90%"],
        ["45 đến dưới 65", "Trung tính", "50% đến 70%"],
        ["25 đến dưới 45", "Phòng thủ", "20% đến 50%"],
        ["0 đến dưới 25", "Rủi ro cao", "0% đến 20%"],
    ], columns=["Market Score", "Trạng thái", "Tỷ trọng cổ phiếu tham chiếu"]), use_container_width=True, hide_index=True)

    st.info(f"Kết luận hiện tại: {result.regime}. Market Score {result.score:.1f}/100, độ tin cậy {result.confidence}. Tỷ trọng cổ phiếu tham chiếu là {result.equity_min:.0%} đến {result.equity_max:.0%}. Đây là mức phân bổ tham chiếu, không phải khuyến nghị mua bán tự động.")
