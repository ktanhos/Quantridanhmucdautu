from __future__ import annotations
import pandas as pd
import streamlit as st
from market_regime import calculate_market_regime


def render_market_regime(index_prices: pd.Series, stock_prices: pd.DataFrame | None = None, volume_data: pd.DataFrame | None = None) -> None:
    st.header("Bước 5. Đánh giá Market Regime")
    st.markdown('<div class="section-note">Đánh giá trạng thái VNINDEX từ xu hướng, động lượng, biến động và thanh khoản. Kết quả này độc lập với tập cổ phiếu đang nghiên cứu.</div>', unsafe_allow_html=True)
    try:
        result = calculate_market_regime(index_prices, None, volume_data)
    except ValueError as exc:
        st.warning(str(exc))
        return

    st.session_state["regime_result"] = result
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Market Score", f"{result.score:.1f} / 100")
    c2.metric("Trạng thái thị trường", result.regime)
    c3.metric("Mức nhất quán tín hiệu", result.confidence)
    c4.metric("Tỷ trọng cổ phiếu tham chiếu", f"{result.equity_min:.0%} đến {result.equity_max:.0%}")
    st.caption("Mức nhất quán tín hiệu cho biết các nhóm chỉ báo đang cùng hướng đến trạng thái hiện tại ở mức nào. Đây không phải đánh giá chất lượng dữ liệu.")

    st.subheader("5.1. Vì sao hệ thống đưa ra trạng thái này?")
    display = result.components.copy()
    display["Điểm"] = display["Điểm"].round(1)
    display["Trọng số"] = display["Trọng số"].map(lambda x: f"{x:.0%}")
    display["Đóng góp"] = display["Đóng góp"].round(1)
    st.dataframe(display, use_container_width=True, hide_index=True)

    with st.expander("Các chỉ báo thị trường", expanded=True):
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
            else:
                text = "N/A" if pd.isna(value) else f"{value:.3f}"
            rows.append({"Chỉ báo": name, "Giá trị": text})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption("Các chỉ báo là bằng chứng định lượng phía sau Market Score. Người dùng có thể xem chúng để hiểu vì sao trạng thái thị trường thay đổi.")

    with st.expander("Ngưỡng phân loại Market Regime", expanded=False):
        thresholds = pd.DataFrame(
            [
                ["80 đến 100", "Tích cực mạnh", "90% đến 100%"],
                ["65 đến dưới 80", "Tích cực", "70% đến 90%"],
                ["45 đến dưới 65", "Trung tính", "50% đến 70%"],
                ["25 đến dưới 45", "Phòng thủ", "20% đến 50%"],
                ["0 đến dưới 25", "Rủi ro cao", "0% đến 20%"],
            ],
            columns=["Market Score", "Trạng thái", "Tỷ trọng cổ phiếu tham chiếu"],
        )
        st.dataframe(thresholds, use_container_width=True, hide_index=True)

    st.info(f"Kết luận hiện tại: {result.regime}. Market Score {result.score:.1f}/100. Các tín hiệu đang nhất quán ở mức {result.confidence}. Tỷ trọng cổ phiếu tham chiếu {result.equity_min:.0%} đến {result.equity_max:.0%}.")
