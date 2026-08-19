import streamlit as st
from portfolio_summary import build_summary


def render_portfolio_summary(performance, regime_result, rebalance_table, target_equity=None):
    st.header("Bước 11. Tổng kết danh mục")
    st.markdown('<div class="section-note">Tóm tắt toàn bộ quy trình thành một vài kết luận dễ đọc: thị trường đang ở trạng thái nào, hiệu quả lịch sử ra sao và tỷ trọng cổ phiếu mục tiêu là bao nhiêu.</div>', unsafe_allow_html=True)
    if performance is None:
        st.info("Chưa có đủ dữ liệu để tổng kết danh mục.")
        return
    needed = bool(rebalance_table is not None and "Cần tái cân bằng" in rebalance_table and rebalance_table["Cần tái cân bằng"].any())
    s = build_summary(performance, regime_result, needed, target_equity)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Trạng thái thị trường", getattr(regime_result, "regime", "Trung tính") if regime_result else "Trung tính")
    c2.metric("Lợi suất quy đổi theo năm", "N/A" if s["cagr"] is None else f"{s['cagr']:.2%}")
    c3.metric("Sharpe Ratio", "N/A" if s["sharpe"] is None else f"{s['sharpe']:.2f}")
    c4.metric("Maximum Drawdown", "N/A" if s["drawdown"] is None else f"{s['drawdown']:.2%}")

    if target_equity is not None:
        st.metric("Tỷ trọng cổ phiếu mục tiêu", f"{target_equity:.1%}")

    st.subheader("11.1. Đánh giá tổng thể")
    st.write(s["regime_text"])
    st.write(s["sharpe_text"])
    st.write(s["drawdown_text"])
    st.write(s["rebalance_text"])

    st.subheader("11.2. Kết luận")
    if needed:
        st.warning("Danh mục đang có độ lệch vượt ngưỡng tái cân bằng đã đặt. Nên xem xét điều chỉnh tỷ trọng về gần danh mục mục tiêu.")
    else:
        st.success("Danh mục hiện tại đang nằm trong ngưỡng tái cân bằng đã đặt. Chưa có tín hiệu bắt buộc phải điều chỉnh tỷ trọng.")
    st.caption("Đây là bản tóm tắt hỗ trợ ra quyết định. Ứng dụng không bảo đảm lợi nhuận và không thay thế quyết định đầu tư của người dùng.")
