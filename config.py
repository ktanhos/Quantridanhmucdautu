from pathlib import Path

APP_NAME = "Quản trị danh mục đầu tư"

CACHE_DIR = Path(".portfolio_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

REQUEST_PAUSE = 1.2
PERIODS_PER_YEAR = 252
DEFAULT_BENCHMARK = "VNINDEX"

DEFAULT_TICKERS = ["GMD", "VCG", "CTR", "HAH", "HPG", "DGC"]
