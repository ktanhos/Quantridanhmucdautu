from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class InvestmentPolicy:
    investor_goal: str
    target_return: float
    risk_tolerance: int
    risk_capacity: int
    investment_horizon_years: int
    liquidity_need: str
    benchmark: str
    max_single_stock_weight: float
    max_sector_weight: float
    allow_short: bool
    allow_leverage: bool
    defensive_asset: str
    emergency_cash_percent: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def risk_label(score: int) -> str:
    if score <= 20:
        return "Rất thận trọng"
    if score <= 40:
        return "Thận trọng"
    if score <= 60:
        return "Cân bằng"
    if score <= 80:
        return "Tăng trưởng"
    return "Tăng trưởng cao"


def validate_policy(policy: InvestmentPolicy) -> list[str]:
    errors: list[str] = []
    if not 0 <= policy.target_return <= 100:
        errors.append("Lợi nhuận mục tiêu phải nằm trong khoảng 0 đến 100 phần trăm.")
    if policy.risk_capacity < policy.risk_tolerance - 20:
        errors.append("Khả năng chịu rủi ro đang thấp hơn đáng kể so với khẩu vị rủi ro. Hãy kiểm tra lại hai câu trả lời.")
    if not 0 < policy.max_single_stock_weight <= 100:
        errors.append("Giới hạn một cổ phiếu phải lớn hơn 0 và không quá 100 phần trăm.")
    if not 0 < policy.max_sector_weight <= 100:
        errors.append("Giới hạn một ngành phải lớn hơn 0 và không quá 100 phần trăm.")
    if policy.emergency_cash_percent < 0 or policy.emergency_cash_percent > 100:
        errors.append("Tỷ lệ tiền dự phòng phải nằm trong khoảng 0 đến 100 phần trăm.")
    return errors
