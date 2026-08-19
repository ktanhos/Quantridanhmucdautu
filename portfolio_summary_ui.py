import numpy as np
import pandas as pd
import streamlit as st
from portfolio_summary import build_summary


def _pct(value):
    return "N/A" if value is None or pd.isna(value) else f"{value:.2%}"


def _ratio(value):
    return "N/A" if value is None or pd.isna(value) else f"{value:.2f}"


def _dashboard_card(title, value, subtitle="", tone="normal"):
    tones={"normal":"#5b8cff","positive":"#2fcf8f","warning":"#f3b94f","negative":"#ff647c"}
    accent=tones.get(tone,tones["normal"])
    st.markdown(f'''<div style="border:1px solid rgba(148,163,184,.16);border-radius:16px;padding:1rem 1.05rem;min-height:112px;background:linear-gradient(145deg,rgba(20,27,39,.92),rgba(12,17,25,.86));box-shadow:0 10px 28px rgba(0,0,0,.12);position:relative;overflow:hidden"><div style="position:absolute;left:0;top:0;bottom:0;width:3px;background:{accent}"></div><div style="font-size:.72rem;color:#8993a4;font-weight:600;margin-bottom:.5rem">{title}</div><div style="font-size:1.48rem;color:#f4f7fb;font-weight:740;letter-spacing:-.025em">{value}</div><div style="font-size:.72rem;color:#657083;margin-top:.42rem;line-height:1.35">{subtitle}</div></div>''',unsafe_allow_html=True)


def _risk_tone(drawdown, sharpe):
    if drawdown is not None and drawdown <= -0.25:return "negative"
    if sharpe is not None and sharpe >= 1:return "positive"
    if sharpe is not None and sharpe < 0:return "warning"
    return "normal"


def render_portfolio_summary(performance, regime_result, rebalance_table, target_equity=None):
    st.header("Bước 11. Tổng kết danh mục")
    st.markdown('<div class="section-note">Đây là màn hình kết luận của toàn bộ quy trình. Các phép tính phía trước không được tính lại; màn hình chỉ tổng hợp kết quả đã có thành thông tin dễ đọc để hỗ trợ quyết định.</div>',unsafe_allow_html=True)
    if performance is None:
        st.info("Chưa có đủ dữ liệu để tổng kết danh mục.")
        return

    needed=bool(rebalance_table is not None and "Cần tái cân bằng" in rebalance_table and rebalance_table["Cần tái cân bằng"].any())
    s=build_summary(performance,regime_result,needed,target_equity)
    regime=getattr(regime_result,"regime","Trung tính") if regime_result else "Trung tính"
    regime_lower=str(regime).lower()
    regime_tone="negative" if any(x in regime_lower for x in ["giảm","bear","xấu"]) else "positive" if any(x in regime_lower for x in ["tăng","bull","tốt"]) else "normal"
    risk_tone=_risk_tone(s.get("drawdown"),s.get("sharpe"))

    st.markdown('''<div style="border:1px solid rgba(91,140,255,.20);border-radius:20px;padding:1.35rem 1.45rem;margin:.4rem 0 1.25rem;background:radial-gradient(circle at 85% 0%,rgba(91,140,255,.14),transparent 32%),linear-gradient(135deg,rgba(17,25,39,.96),rgba(10,15,23,.94));box-shadow:0 16px 45px rgba(0,0,0,.16)"><div style="font-size:.72rem;color:#7f8a9d;text-transform:uppercase;letter-spacing:.12em;font-weight:700">Investment Dashboard</div><div style="font-size:1.6rem;font-weight:760;color:#f5f7fb;margin-top:.25rem">Đánh giá nhanh danh mục</div><div style="font-size:.86rem;color:#8993a4;margin-top:.35rem;max-width:850px;line-height:1.55">Từ trạng thái thị trường, hiệu quả lịch sử và rủi ro, hệ thống đưa ra một bức tranh tổng hợp. Đây là dữ liệu hỗ trợ quyết định, không phải cam kết lợi nhuận.</div></div>''',unsafe_allow_html=True)

    st.subheader("11.1. Bốn chỉ tiêu cần nhìn trước")
    c1,c2,c3,c4=st.columns(4)
    with c1:_dashboard_card("Trạng thái thị trường",regime,"Tín hiệu được xác định từ VNINDEX",regime_tone)
    with c2:_dashboard_card("Lợi suất quy đổi theo năm",_pct(s.get("cagr")),"Kết quả lịch sử trong giai đoạn đánh giá","positive" if s.get("cagr") is not None and s["cagr"]>0 else "negative")
    with c3:_dashboard_card("Sharpe Ratio",_ratio(s.get("sharpe")),"Hiệu quả trên mỗi đơn vị tổng rủi ro",risk_tone)
    with c4:_dashboard_card("Maximum Drawdown",_pct(s.get("drawdown")),"Mức giảm lớn nhất từ đỉnh xuống đáy",risk_tone)

    if target_equity is not None:
        st.subheader("11.2. Phân bổ mục tiêu")
        c1,c2,c3=st.columns(3)
        c1.metric("Tỷ trọng cổ phiếu",f"{target_equity:.1%}")
        c2.metric("Tỷ trọng phòng thủ",f"{max(0,1-float(target_equity)):.1%}")
        c3.metric("Trạng thái tái cân bằng","Cần xem xét" if needed else "Chưa cần")
        st.caption("Tỷ trọng phòng thủ là phần vốn không phân bổ vào cổ phiếu theo phương án mục tiêu hiện tại.")

    st.subheader("11.3. Đọc kết quả theo ngôn ngữ đơn giản")
    explanations=[("Thị trường",s.get("regime_text","")),("Hiệu quả điều chỉnh theo rủi ro",s.get("sharpe_text","")),("Mức sụt giảm",s.get("drawdown_text","")),("Tái cân bằng",s.get("rebalance_text",""))]
    for title,text in explanations:
        if text:
            st.markdown(f'''<div style="border:1px solid rgba(148,163,184,.13);border-radius:12px;padding:.78rem .95rem;margin:.45rem 0;background:rgba(15,21,31,.62)"><div style="font-size:.74rem;color:#8f99aa;font-weight:650;margin-bottom:.2rem">{title}</div><div style="font-size:.84rem;color:#d8dee8;line-height:1.55">{text}</div></div>''',unsafe_allow_html=True)

    st.subheader("11.4. Kết luận")
    if needed:
        st.warning("Danh mục đang có độ lệch vượt ngưỡng tái cân bằng đã đặt. Nên xem xét điều chỉnh tỷ trọng về gần danh mục mục tiêu.")
    else:
        st.success("Danh mục hiện tại đang nằm trong ngưỡng tái cân bằng đã đặt. Chưa có tín hiệu bắt buộc phải điều chỉnh tỷ trọng.")

    st.markdown('''<div style="border:1px solid rgba(91,140,255,.16);border-radius:14px;padding:1rem 1.1rem;margin-top:.8rem;background:rgba(91,140,255,.045)"><div style="font-size:.78rem;color:#aeb8c8;font-weight:650;margin-bottom:.35rem">Cách sử dụng màn hình này</div><div style="font-size:.82rem;color:#8993a4;line-height:1.6">Nếu kết quả chưa phù hợp, quay lại Hồ sơ đầu tư hoặc Tập cổ phiếu để thay đổi đầu vào rồi chạy lại quy trình. Không nên cố điều chỉnh tỷ trọng thủ công chỉ để đạt một chỉ tiêu riêng lẻ.</div></div>''',unsafe_allow_html=True)
    st.caption("Các kết quả lịch sử không bảo đảm lợi nhuận tương lai. Ứng dụng chỉ hỗ trợ định hướng quản trị danh mục và không đặt lệnh thay người dùng.")
