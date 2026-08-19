from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class RegimeResult:
    score: float
    regime: str
    confidence: str
    equity_min: float
    equity_max: float
    components: pd.DataFrame
    indicators: dict

def _score_linear(value: float, low: float, high: float) -> float:
    if not np.isfinite(value): return 50.0
    return float(np.clip((value - low) / (high - low) * 100.0, 0.0, 100.0))

def _score_ratio(value: float, neutral: float, strong: float) -> float:
    if not np.isfinite(value): return 50.0
    return float(np.clip((value - neutral) / (strong - neutral) * 50.0 + 50.0, 0.0, 100.0))

def _trend_score(index: pd.Series):
    ma50, ma200 = index.rolling(50).mean(), index.rolling(200).mean()
    r50 = index.iloc[-1] / ma50.iloc[-1] if pd.notna(ma50.iloc[-1]) else np.nan
    r200 = index.iloc[-1] / ma200.iloc[-1] if pd.notna(ma200.iloc[-1]) else np.nan
    slope = ma50.iloc[-1] / ma50.iloc[-21] - 1 if pd.notna(ma50.iloc[-21]) else np.nan
    return 0.4*_score_ratio(r50,.98,1.04)+0.4*_score_ratio(r200,.98,1.06)+0.2*_score_linear(slope,-.05,.05), {"VNINDEX / MA50":r50,"VNINDEX / MA200":r200,"MA50 21D change":slope}

def _breadth_score(stock_prices):
    if stock_prices is None or stock_prices.empty: return 50.0, {}
    a50=[]; a200=[]
    for col in stock_prices.columns:
        s=pd.to_numeric(stock_prices[col],errors="coerce").dropna()
        if len(s)>=50: a50.append(float(s.iloc[-1]>s.rolling(50).mean().iloc[-1]))
        if len(s)>=200: a200.append(float(s.iloc[-1]>s.rolling(200).mean().iloc[-1]))
    p50=np.mean(a50)*100 if a50 else np.nan; p200=np.mean(a200)*100 if a200 else np.nan
    return float(np.nanmean([p50,p200])) if np.isfinite(p50) or np.isfinite(p200) else 50.0,{"% stocks above MA50":p50,"% stocks above MA200":p200,"Stocks analyzed":stock_prices.shape[1]}

def _liquidity_score(volumes):
    if volumes is None or volumes.empty: return 50.0, np.nan
    v=volumes.apply(pd.to_numeric,errors="coerce").tail(60)
    daily=v.sum(axis=1)
    if len(daily)<20: return 50.0,np.nan
    ratio=daily.tail(20).mean()/daily.mean() if daily.mean()!=0 else np.nan
    return _score_ratio(ratio,.90,1.10),ratio

def calculate_market_regime(index_prices, stock_prices=None, volumes=None):
    index=pd.to_numeric(index_prices,errors="coerce").dropna().sort_index()
    if len(index)<60: raise ValueError("Cần tối thiểu 60 phiên dữ liệu VNINDEX để xác định Market Regime.")
    trend_score,trend=_trend_score(index); breadth_score,breadth=_breadth_score(stock_prices)
    ret20=index.iloc[-1]/index.iloc[-21]-1; ret60=index.iloc[-1]/index.iloc[-61]-1; ret120=index.iloc[-1]/index.iloc[-121]-1 if len(index)>120 else np.nan
    momentum_score=float(np.nanmean([_score_linear(ret20,-.10,.10),_score_linear(ret60,-.20,.20),_score_linear(ret120,-.30,.30)]))
    daily=index.pct_change().dropna(); vol20=daily.tail(20).std()*np.sqrt(252); vol60=daily.tail(60).std()*np.sqrt(252)
    vol_score=_score_linear(vol20,.45,.10); drawdown=index.iloc[-1]/index.cummax().iloc[-1]-1; risk_score=.7*vol_score+.3*_score_linear(drawdown,-.30,0)
    liquidity_score,liquidity_ratio=_liquidity_score(volumes)
    weights={"Trend":.30,"Breadth":.25,"Momentum":.20,"Volatility & Drawdown":.15,"Liquidity":.10}
    scores={"Trend":trend_score,"Breadth":breadth_score,"Momentum":momentum_score,"Volatility & Drawdown":risk_score,"Liquidity":liquidity_score}
    score=sum(scores[k]*weights[k] for k in weights)
    if score>=80: regime,equity="Tích cực mạnh",(.90,1.00)
    elif score>=65: regime,equity="Tích cực",(.70,.90)
    elif score>=45: regime,equity="Trung tính",(.50,.70)
    elif score>=25: regime,equity="Phòng thủ",(.20,.50)
    else: regime,equity="Rủi ro cao",(0,.20)
    dispersion=np.std(list(scores.values())); confidence="Cao" if dispersion<10 else "Trung bình" if dispersion<20 else "Thấp"
    components=pd.DataFrame({"Nhóm chỉ báo":list(weights),"Điểm":[scores[k] for k in weights],"Trọng số":[weights[k] for k in weights],"Đóng góp":[scores[k]*weights[k] for k in weights]})
    indicators={**trend,**breadth,"Return 20D":ret20,"Return 60D":ret60,"Return 120D":ret120,"Volatility 20D":vol20,"Volatility 60D":vol60,"Current Drawdown":drawdown,"Liquidity 20D / 60D":liquidity_ratio}
    return RegimeResult(score,regime,confidence,equity[0],equity[1],components,indicators)
