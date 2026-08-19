from dataclasses import dataclass

@dataclass(frozen=True)
class TradingCosts:
    trading_fee_rate: float = 0.001
    sell_tax_rate: float = 0.001
    custody_fee_per_share_month: float = 0.27
    margin_interest_rate: float = 0.12

    def summary(self):
        return {'Phí giao dịch mua/bán': self.trading_fee_rate,'Thuế thu nhập cá nhân khi bán': self.sell_tax_rate,'Phí lưu ký mỗi cổ phiếu mỗi tháng': self.custody_fee_per_share_month,'Lãi suất vay Margin mỗi năm': self.margin_interest_rate}
