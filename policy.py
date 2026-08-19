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
    risk_free_rate: float = 0.04

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def risk_label(score: int) -> str:
    if score <= 33:
        return "Thận trọng"
    if score <= 66:
        return "Cân bằng"
    return "Tăng trưởng"


def risk_profile_description(score: int) -> str:
    if score <= 33:
        return "Ưu tiên hạn chế biến động và mức giảm của danh mục. Phù hợp nếu bạn khó chấp nhận việc danh mục giảm mạnh trong ngắn hạn."
    if score <= 66:
        return "Chấp nhận biến động ở mức vừa phải để đổi lấy khả năng tăng trưởng dài hạn tốt hơn."
    return "Chấp nhận biến động lớn hơn và có thể chịu các giai đoạn giảm mạnh để tìm kiếm mức tăng trưởng cao hơn."


def validate_policy(policy: InvestmentPolicy) -> list[str]:
    errors: list[str] = []
    if not 0 <= policy.target_return <= 1:
        errors.append("Lợi nhuận mục tiêu phải nằm trong khoảng 0 đến 100 phần trăm.")
    if not 0 <= policy.risk_tolerance <= 100 or not 0 <= policy.risk_capacity <= 100:
        errors.append("Mức chấp nhận biến động phải nằm trong khoảng 0 đến 100.")
    if not 0 < policy.max_single_stock_weight <= 1:
        errors.append("Giới hạn một cổ phiếu phải lớn hơn 0 và không quá 100 phần trăm.")
    if not 0 < policy.max_sector_weight <= 1:
        errors.append("Giới hạn một ngành phải lớn hơn 0 và không quá 100 phần trăm.")
    if not 0 <= policy.risk_free_rate <= 1:
        errors.append("Lãi suất phi rủi ro phải nằm trong khoảng 0 đến 100 phần trăm.")
    return errors
