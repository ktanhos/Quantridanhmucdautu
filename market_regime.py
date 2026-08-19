from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class RegimeResult:
    score: float; regime: str; confidence: str; equity_min: float; equity_max: float; components: pd.DataFrame; indicators: dict

def _score_linear(value, low, high):
    if not np.isfinite(value): return 50.0
    return float(np.clip((value-low)/(high-low)*100,0,100))

def _score_ratio(value, neutral, strong):
    if not np.isfinite(value): return 50.0
    return float(np.clip((value-neutral)/(strong-neutral)*50+50,0,100))

def _trend_score(index):
    ma50=index.rolling(50).mean(); ma200=index.rolling(200).mean()
    r50=index.iloc[-1]/ma50.iloc[-1] if pd.notna(ma50.iloc[-1]) else np.nan
    r200=index.iloc[-1]/ma200.iloc[-1] if pd.notna(ma200.iloc[-1]) else np.nan
    slope=ma50.iloc[-1]/ma50.iloc[-21]-1 if pd.notna(ma50.iloc[-21]) else np.nan
    score=.4*_score_ratio(r50,.98,1.04)+.4*_score_ratio(r200,.98,1.06)+.2*_score_linear(slope,-.05,.05)
    return score,{'VNINDEX / MA50':r50,'VNINDEX / MA200':r200,'MA50 21D change':slope}

def _liquidity_score(volume):
    if volume is None:return 50.,np.nan
    v=pd.to_numeric(volume,errors='coerce').dropna()
    if len(v)<60:return 50.,np.nan
    ratio=v.tail(20).mean()/v.tail(60).mean() if v.tail(60).mean()!=0 else np.nan
    return _score_ratio(ratio,.90,1.10),ratio

def calculate_market_regime(index_prices,stock_prices=None,volumes=None):
    index=pd.to_numeric(index_prices,errors='coerce').dropna().sort_index()
    if len(index)<60:raise ValueError('Cần tối thiểu 60 phiên dữ liệu VNINDEX để xác định Market Regime.')
    trend_score,trend=_trend_score(index)
    ret20=index.iloc[-1]/index.iloc[-21]-1; ret60=index.iloc[-1]/index.iloc[-61]-1; ret120=index.iloc[-1]/index.iloc[-121]-1 if len(index)>120 else np.nan
    momentum_score=float(np.nanmean([_score_linear(ret20,-.1,.1),_score_linear(ret60,-.2,.2),_score_linear(ret120,-.3,.3)]))
    daily=index.pct_change().dropna(); vol20=daily.tail(20).std()*np.sqrt(252); vol60=daily.tail(60).std()*np.sqrt(252)
    drawdown=index.iloc[-1]/index.cummax().iloc[-1]-1; risk_score=.7*_score_linear(vol20,.45,.10)+.3*_score_linear(drawdown,-.30,0)
    liquidity_score,liquidity_ratio=_liquidity_score(volumes)
    weights={'Trend':.35,'Momentum':.25,'Volatility & Drawdown':.20,'Liquidity':.20};scores={'Trend':trend_score,'Momentum':momentum_score,'Volatility & Drawdown':risk_score,'Liquidity':liquidity_score};score=sum(scores[k]*weights[k] for k in weights)
    if score>=80:reg,equity='Tích cực mạnh',(.90,1.00)
    elif score>=65:reg,equity='Tích cực',(.70,.90)
    elif score>=45:reg,equity='Trung tính',(.50,.70)
    elif score>=25:reg,equity='Phòng thủ',(.20,.50)
    else:reg,equity='Rủi ro cao',(0,.20)
    dispersion=np.std(list(scores.values()));confidence='Cao' if dispersion<10 else 'Trung bình' if dispersion<20 else 'Thấp'
    components=pd.DataFrame({'Nhóm chỉ báo':list(weights),'Điểm':[scores[k] for k in weights],'Trọng số':[weights[k] for k in weights],'Đóng góp':[scores[k]*weights[k] for k in weights]})
    indicators={**trend,'Return 20D':ret20,'Return 60D':ret60,'Return 120D':ret120,'Volatility 20D':vol20,'Volatility 60D':vol60,'Current Drawdown':drawdown,'VNINDEX Volume 20D / 60D':liquidity_ratio}
    return RegimeResult(score,reg,confidence,equity[0],equity[1],components,indicators)
