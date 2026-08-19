import time
from pathlib import Path
import numpy as np
import pandas as pd
from vnstock import Market, Fundamental, Reference, register_user
from config import CACHE_DIR, REQUEST_PAUSE

def configure_vnstock(api_key=None):
    api_key=(api_key or "").strip()
    if not api_key:return {"authenticated":False,"message":"Đang dùng chế độ khách của Vnstock."}
    register_user(api_key=api_key);return {"authenticated":True,"message":"Đã xác thực API key Vnstock."}
def pause_api():time.sleep(REQUEST_PAUSE)
def cache_path(kind,key):return CACHE_DIR/f"{kind}_{str(key).replace('/','_').replace('\\','_').replace(':','_')}.csv"
def normalize_columns(df):
    if df is None:return pd.DataFrame()
    out=df.copy();out.columns=[str(c).strip().lower().replace(' ','_').replace('-','_') for c in out.columns];return out
def safe_float(value):
    try:
        if pd.isna(value):return np.nan
        if isinstance(value,str):value=value.replace(',','').replace('%','').strip()
        return float(value)
    except:return np.nan
def find_col(df,candidates):
    if df.empty:return None
    return next((c for c in candidates if c in df.columns),None)
def _extract_ohlcv(df):
    df=normalize_columns(df)
    if df.empty or 'close' not in df.columns:return pd.DataFrame()
    date_col='time' if 'time' in df.columns else 'date'
    if date_col not in df.columns:return pd.DataFrame()
    df[date_col]=pd.to_datetime(df[date_col]);out=df.set_index(date_col).sort_index();keep=[c for c in ['open','high','low','close','volume'] if c in out.columns]
    for c in keep:out[c]=pd.to_numeric(out[c],errors='coerce')
    return out[keep]
def _get_equity_ohlcv(ticker,start_date,end_date):
    market=Market();start_ts=pd.Timestamp(start_date);end_ts=pd.Timestamp(end_date);count=max(int((end_ts-start_ts).days*.72)+50,300);raw=market.equity(ticker).ohlcv(end=end_date,interval='1D',count=count);out=_extract_ohlcv(raw);return out[(out.index>=start_ts)&(out.index<=end_ts)]
def get_price_data(tickers,start_date,end_date):
    output={}
    for ticker in tickers:
        path=cache_path('price',f'{ticker}_{start_date}_{end_date}')
        try:
            if path.exists():cached=pd.read_csv(path,parse_dates=['Date'],index_col='Date');output[ticker]=pd.to_numeric(cached['close'],errors='coerce');continue
            ohlcv=_get_equity_ohlcv(ticker,start_date,end_date)
            if ohlcv.empty:continue
            ohlcv.rename_axis('Date').to_csv(path);output[ticker]=ohlcv['close'];pause_api()
        except Exception as exc:print(f'Lỗi lấy giá {ticker}: {exc}')
    out=pd.DataFrame(output).sort_index();out.index=pd.to_datetime(out.index).normalize();out.index.name='Date';return out
def get_volume_data(tickers,start_date,end_date):
    output={}
    for ticker in tickers:
        path=cache_path('volume',f'{ticker}_{start_date}_{end_date}')
        try:
            if path.exists():cached=pd.read_csv(path,parse_dates=['Date'],index_col='Date');output[ticker]=pd.to_numeric(cached['volume'],errors='coerce');continue
            ohlcv=_get_equity_ohlcv(ticker,start_date,end_date)
            if 'volume' not in ohlcv.columns:continue
            ohlcv[['volume']].rename_axis('Date').to_csv(path);output[ticker]=ohlcv['volume'];pause_api()
        except Exception as exc:print(f'Lỗi lấy khối lượng {ticker}: {exc}')
    out=pd.DataFrame(output).sort_index();out.index=pd.to_datetime(out.index).normalize();out.index.name='Date';return out

def get_benchmark_ohlcv(benchmark,start_date,end_date):
    market=Market();start_ts=pd.Timestamp(start_date).normalize();end_ts=pd.Timestamp(end_date).normalize();pieces=[];cursor=start_ts
    while cursor<=end_ts:
        chunk_end=min(cursor+pd.Timedelta(days=119),end_ts);path=cache_path('benchmark_ohlcv',f'{benchmark}_{cursor:%Y%m%d}_{chunk_end:%Y%m%d}');df=None
        if path.exists():
            try:df=pd.read_csv(path,parse_dates=['Date'],index_col='Date')
            except:df=None
        if df is None or df.empty:
            df=_extract_ohlcv(market.index(benchmark).ohlcv(start=cursor.strftime('%Y-%m-%d'),end=chunk_end.strftime('%Y-%m-%d'),interval='1D'))
            if df.empty:raise ValueError(f'Không lấy được OHLCV benchmark {benchmark}')
            df.rename_axis('Date').to_csv(path);pause_api()
        pieces.append(df);cursor=chunk_end+pd.Timedelta(days=1)
    out=pd.concat(pieces);out=out[~out.index.duplicated(keep='last')].sort_index();return out[(out.index>=start_ts)&(out.index<=end_ts)]
def get_benchmark_prices(benchmark,start_date,end_date):return get_benchmark_ohlcv(benchmark,start_date,end_date)['close']

def get_company_table(tickers,prices=None):
    ref=Reference();rows=[]
    try:sectors=normalize_columns(ref.industry.sectors())
    except:sectors=pd.DataFrame()
    sector_symbol=find_col(sectors,['symbol','ticker','stock_code','code']);sector_name=find_col(sectors,['icb_name_vi','icb_name','industry_name_vi','industry_name','industry'])
    for ticker in tickers:
        try:
            path=cache_path('company',ticker);info=normalize_columns(pd.read_csv(path)) if path.exists() else normalize_columns(ref.company(ticker).info())
            if not path.exists():info.to_csv(path,index=False);pause_api()
            industry=np.nan
            if sector_symbol and sector_name:
                m=sectors[sectors[sector_symbol].astype(str).str.upper()==ticker]
                if not m.empty:industry=m.iloc[0][sector_name]
            shares=np.nan;sc=find_col(info,['issue_share','shares_outstanding','outstanding_shares','listed_shares'])
            if sc:shares=safe_float(info.iloc[0][sc])
            cap=np.nan
            if prices is not None and ticker in prices.columns and pd.notna(shares):cap=float(prices[ticker].dropna().iloc[-1])*shares*1000
            rows.append({'Mã':ticker,'Ngành':industry,'Số CP lưu hành':shares,'Vốn hóa':cap})
        except Exception:rows.append({'Mã':ticker,'Ngành':np.nan,'Số CP lưu hành':np.nan,'Vốn hóa':np.nan})
    return pd.DataFrame(rows)
def get_income_data(tickers):
    fun=Fundamental();rows=[]
    for ticker in tickers:
        try:
            path=cache_path('income',ticker);income=normalize_columns(pd.read_csv(path)) if path.exists() else normalize_columns(fun.equity(ticker).income_statement(period='year',orient='report'))
            if not path.exists():income.to_csv(path,index=False);pause_api()
            item_col=find_col(income,['item','item_name','name','indicator']);years=sorted([c for c in income.columns if str(c).isdigit() and len(str(c))==4],key=lambda x:int(str(x)),reverse=True);revenue=profit=np.nan;ry=py=None
            if item_col and years:
                items=income[item_col].astype(str).str.lower()
                for key in ['doanh thu thuan','net revenue','revenue','tong thu nhap hoat dong']:
                    m=items.str.contains(key,regex=False,na=False)
                    if m.any():
                        row=income.loc[m].iloc[0]
                        for y in years:
                            v=safe_float(row[y])
                            if pd.notna(v):revenue,ry=v,str(y);break
                    if pd.notna(revenue):break
                for key in ['loi nhuan sau thue cua co dong cong ty me','loi nhuan sau thue','profit after tax','net profit']:
                    m=items.str.contains(key,regex=False,na=False)
                    if m.any():
                        row=income.loc[m].iloc[0]
                        for y in years:
                            v=safe_float(row[y])
                            if pd.notna(v):profit,py=v,str(y);break
                    if pd.notna(profit):break
            rows.append({'Mã':ticker,'Doanh thu gần nhất':revenue,'Năm doanh thu':ry,'LNST gần nhất':profit,'Năm LNST':py})
        except Exception:rows.append({'Mã':ticker,'Doanh thu gần nhất':np.nan,'Năm doanh thu':None,'LNST gần nhất':np.nan,'Năm LNST':None})
    return pd.DataFrame(rows)
