#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions and helpers for RealFin tools.

This module contains all helper functions extracted from tool_library.py
that are used by the 85 main tool functions.
"""

# ============================================================================
# IMPORTS
# ============================================================================
import akshare as ak
import pandas as pd
import numpy as np
import time, re, requests, os, json
from io import StringIO
import unicodedata
import unittest
import traceback
import pickle

from functools import lru_cache
from datetime import datetime, timedelta, date
from typing import Optional, Any, Dict, Callable, Tuple, Union, List, Literal

# ============================================================================
# GLOBAL VARIABLES AND CONSTANTS
# ============================================================================
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY", "YOUR_CURRENCY_API_KEY")

_VERBOSE_LOGGING = os.getenv("TOOL_LIBRARY_VERBOSE", "").lower() in ("1", "true", "yes")

LOCAL_PICKLE_FILE = os.path.join(os.path.dirname(__file__), 'local_data_archive.pkl')

_stock_data_cache: Dict[str, Optional[pd.DataFrame]] = {}

STOCK_DATA_KEYS: Dict[str, Tuple[str, str]] = {
    'a_shares': ('a_name_code', '名称', '代码'),
    'hk_shares': ('hk_name_code', '中文名称', '代码'),
    'us_shares': ('us_name_code_market', '名称', '代码'),
}

_stock_data_cache: Dict[str, Optional[pd.DataFrame]] = {}

_a_history_cache: Dict[tuple, pd.DataFrame] = {}

LATEST_KEYWORDS = ['最新', 'latest', 'newest', 'today', '今天', '当前', '实时']

_a_spot_cache: Optional[pd.DataFrame] = None

_a_spot_cache_time: Optional[datetime] = None

_us_spot_cache: Optional[pd.DataFrame] = None

_us_spot_cache_time: Optional[datetime] = None

US_SPOT_CACHE_EXPIRY_SECONDS = 600 

_hk_spot_cache: Optional[pd.DataFrame] = None

_hk_spot_cache_time: Optional[datetime] = None

HK_SPOT_CACHE_EXPIRY_SECONDS = 600 

MAX_API_RETRIES = 3 

RETRY_SLEEP_SECONDS = 120 

_hk_history_cache_akshare: Dict[Tuple, Optional[pd.DataFrame]] = {}

HK_STOCK_CACHE_EXPIRY_SECONDS = 3600 # 缓存 1 小时

LATEST_KEYWORDS = ['最新', 'latest', 'newest', 'today', '今天', '当前', '实时']

_index_data_cache: Dict[str, Optional[pd.DataFrame]] = {}

_us_index_history_cache: Dict[str, Optional[pd.DataFrame]] = {}

INDEX_API_MAP: Dict[str, callable] = {
    'hk_index': lambda: ak.stock_hk_index_spot_sina(),
    'a_index': lambda: ak.stock_zh_index_spot_sina(),
    'global_index': lambda: ak.index_global_spot_em(), 
    'us_index': lambda: pd.DataFrame() 
}

_COLUMN_MAP_AK_TO_STD = {
    'date': 'date', 'open': 'open', 'close': 'close', 'high': 'high', 'low': 'low',
    'volume': 'volume', 'turnover': 'turnover', '日期': 'date', '开盘': 'open',
    '今开': 'open', '收盘': 'close', '最新价': 'close', 'latest': 'close', '最高': 'high',
    '高': 'high', '最低': 'low', '低': 'low', '成交量': 'volume', '成交额': 'turnover',
    'amount': 'turnover',
}

# ALIAS_TO_STANDARD_NAME_MAP will be defined after normalize_name function

_index_spot_caches: Dict[str, Optional[pd.DataFrame]] = {}

_index_spot_cache_times: Dict[str, Optional[datetime]] = {}

INDEX_SPOT_CACHE_EXPIRY_SECONDS = 3600 # 缓存过期时间设置为 1h

_index_data_cache: Dict[str, Optional[pd.DataFrame]] = {}

_us_index_history_cache: Dict[str, Optional[pd.DataFrame]] = {} # 历史缓存不变

INDEX_DATA_KEYS: Dict[str, Tuple[str, str, str]] = {
    # Key: (Pickle Archive Key, Name Column, Code Column)
    'a_index': ('a_index_data', '名称', '代码'),
    'hk_index': ('hk_index_data', '名称', '代码'),
    'global_index': ('global_index_data', '名称', '代码'),
    'us_index': ('us_index_data', '名称', '代码'), 
}

_a_history_cache: Dict[tuple, pd.DataFrame] = {}

_a_dividend_payout_cache: Dict[str, pd.DataFrame] = {}

CACHE_TTL_SECONDS = 60

_spot_market_cache: Dict[str, Optional[pd.DataFrame]] = {}

_balance_sheet_cache: Dict[str, pd.DataFrame] = {}

_car_market_cache: Dict[tuple, pd.DataFrame] = {}

_api_cache = {}

_population_cache: Optional[pd.DataFrame] = None

_dividend_allotment_cache: Dict[str, pd.DataFrame] = {}

_earnings_announcement_cache: Dict[str, pd.DataFrame] = {}

_earnings_report_cache: Dict[str, pd.DataFrame] = {}

_financial_indicators_cache: Dict[str, pd.DataFrame] = {}

FOREIGN_FUTURES_ALIAS_MAP: Dict[str, str] = {
    'wti': 'NYMEX原油', 'wticrudeoil': 'NYMEX原油', 'nymexcrudeoil': 'NYMEX原油', 'cl': 'NYMEX原油',
    'brent': '布伦特原油', 'brentcrudeoil': '布伦特原油', 'co': '布伦特原油',
    'gold': 'COMEX黄金', 'comexgold': 'COMEX黄金', 'gc': 'COMEX黄金',
    'silver': 'COMEX白银', 'comexsilver': 'COMEX白银', 'si': 'COMEX白银',
    'COMEX copper': 'COMEX铜', 'naturalgas': 'NYMEX天然气', 'ng': 'NYMEX天然气',
    'lme尼克尔': 'LME镍3个月',
}

_fx_spot_quote_cache: Dict[str, Any] = {"data": None, "timestamp": 0}

_global_spot_cache: Optional[pd.DataFrame] = None

_cache_timestamp: float = 0

CACHE_TTL_SECONDS: int = 300  

INDEX_ALIAS_MAP = {
    # 美国指数
    'sp500': 'SPX', 's&p500': 'SPX', '标普500': 'SPX', 'S&P 500': 'SPX',
    'dowjones': 'DJIA', 'dow': 'DJIA', '道琼斯': 'DJIA',
    'nasdaq': 'NDX', '纳斯达克': 'NDX',
    
    # 亚洲指数
    'hangseng': 'HSI', 'hsi': 'HSI', '恒生指数': 'HSI',
    'nikkei225': 'N225', 'nikkei': 'N225', '日经225': 'N225',
    'kospi': 'KS11', '韩国kospi': 'KS11',
    'jakartacomposite': 'JKSE', 'idxcomposite': 'JKSE', '印尼雅加达综合': 'JKSE',
    
    # 欧洲指数
    'ftse100': 'FTSE', 'uk100': 'FTSE', '富时100': 'FTSE',
    'dax': 'GDAXI', 'dax30': 'GDAXI', '德国dax30': 'GDAXI',
    'cac40': 'FCHI', '法国cac40': 'FCHI', '德国DAX30': 'GDAXI',

    # 其他
    '上证指数': '000001', '沪深300': '000300', '创业板指': '399006',
    'allordinaries': 'AORD'
}

_income_statement_cache: Dict[str, pd.DataFrame] = {}

_financial_abstract_cache: Dict[str, pd.DataFrame] = {}

_benchmark_cache: Dict[str, pd.DataFrame] = {}

_sge_report_cache: Optional[pd.DataFrame] = None

_stock_comment_cache: Optional[pd.DataFrame] = None

_ths_forecast_cache: Dict[tuple, Optional[pd.DataFrame]] = {}

_ths_forecast_cache: Dict[tuple, Optional[pd.DataFrame]] = {}

_earnings_announcement_cache: Dict[str, Optional[pd.DataFrame]] = {}

_stock_zh_a_hist_cache: Dict[Tuple, Optional[pd.DataFrame]] = {}

_stock_zh_a_hist_tx_cache: Dict[Tuple, Optional[pd.DataFrame]] = {}

_long_stock_financial_cache = {}

_top_10_sh_cache: Dict[tuple, pd.DataFrame] = {}

_forex_hist_cache: Dict[str, pd.DataFrame] = {}

_INDEX_DATA_CACHE: Optional[pd.DataFrame] = None

PICKLE_INDEX_KEY = 'index_stock_info'

InfoType = Literal["code", "publish_date"]

PICKLE_KEY_A = 'a_name_code'

PICKLE_KEY_HK = 'hk_name_code'

PICKLE_KEY_US = 'us_name_code_market'


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def _log_debug(msg: str):
    """内部日志函数：只在详细日志模式下输出"""
    if _VERBOSE_LOGGING:
        print(msg)


def _get_price_day_tx(code, end_date='', count=10, frequency='1d', adjust='qfq'):
    unit='week' if frequency in '1w' else 'month' if frequency in '1M' else 'day'
    if end_date:
        end_date=end_date.strftime('%Y-%m-%d') if isinstance(end_date, date) else end_date.split(' ')[0]
    end_date='' if end_date==datetime.now().strftime('%Y-%m-%d') else end_date
    adjust_param = 'qfq'
    if adjust == 'hfq':
        adjust_param = 'hfq'
    elif adjust == '':
        adjust_param = '' 
    URL=f'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},{unit},,{end_date},{count},{adjust_param}'
    st= json.loads(requests.get(URL).content)
    if st.get('code') != 0 or 'data' not in st or code not in st['data']:
        _log_debug(f"  -> [Tencent] 失败: API 未返回 '{code}' 的有效数据。Msg: {st.get('msg')}")
        return None
    stk = st['data'][code]
    if not isinstance(stk, dict):
        _log_debug(f"  -> [Tencent] 失败: API 为 '{code}' 返回了非预期的格式 (非字典)。")
        return None
    ms = f'{adjust_param}{unit}' if adjust_param else unit
    buf=stk.get(ms)
    if buf is None:
        buf = stk.get(unit)
    if buf is None:
        _log_debug(f"  -> [Tencent] 失败: 在 API 响应中未找到 '{ms}' 或 '{unit}' 键。")
        return None
    df=pd.DataFrame(buf,columns=['time','open','close','high','low','volume'],dtype='float')
    df.time=pd.to_datetime(df.time);
    df.set_index(['time'], inplace=True);
    df.index.name='' 
    return df


def _get_price_min_tx(code, end_date=None, count=10, frequency='1d'):
    ts=int(frequency[:-1]) if frequency[:-1].isdigit() else 1
    if end_date: end_date=end_date.strftime('%Y-%m-%d') if isinstance(end_date, date) else end_date.split(' ')[0]
    URL=f'http://ifzq.gtimg.cn/appstock/app/kline/mkline?param={code},m{ts},,{count}'
    try:
        st= json.loads(requests.get(URL).content)
        if 'data' not in st or code not in st['data'] or 'm'+str(ts) not in st['data'][code]:
            _log_debug(f"  -> [Tencent Min] 失败: API 未返回 'm{ts}' 数据 for {code}。")
            return None 
        buf = st['data'][code]['m'+str(ts)]
        if not buf:
            _log_debug(f"  -> [Tencent Min] 失败: API 返回了 'm{ts}' 的空列表 (code: {code} 可能不受支持)。")
            return None 
        df = pd.DataFrame(buf, columns=['time','open','close','high','low','volume','n1','n2'])
        df = df[['time','open','close','high','low','volume']]
        df[['open','close','high','low','volume']] = df[['open','close','high','low','volume']].astype('float')
        df.time=pd.to_datetime(df.time);  df.set_index(['time'], inplace=True);  df.index.name=''
        if not df.empty and 'qt' in st['data'][code] and code in st['data'][code]['qt']:
            df.iloc[-1, df.columns.get_loc('close')] = float(st['data'][code]['qt'][code][3])
        return df
    except Exception as e:
        _log_debug(f"  -> [Tencent Min] 失败: 处理 {code} 时发生意外错误: {e}")
        return None


def _get_price_sina(code, end_date='', count=10, frequency='60m'):
    frequency=frequency.replace('1d','240m').replace('1w','1200m').replace('1M','7200m');
    mcount=count
    ts=int(frequency[:-1]) if frequency[:-1].isdigit() else 1
    if (end_date!='') & (frequency in ['240m','1200m','7200m']): 
        end_date=pd.to_datetime(end_date) if not isinstance(end_date, date) else end_date
        unit=4 if frequency=='1200m' else 29 if frequency=='7200m' else 1
        count=count+(datetime.now()-end_date).days//unit
    URL=f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={code}&scale={ts}&ma=5&datalen={count}' 
    dstr= json.loads(requests.get(URL).content);
    if not isinstance(dstr, list):
        _log_debug(f"  -> [Sina] 失败: API 未返回列表数据 (可能是不支持的 code: {code})。")
        return None 
    df= pd.DataFrame(dstr,columns=['day','open','high','low','close','volume'])
    df['open'] = df['open'].astype(float); df['high'] = df['high'].astype(float);
    df['low'] = df['low'].astype(float);  df['close'] = df['close'].astype(float);  df['volume'] = df['volume'].astype(float)
    df.day=pd.to_datetime(df.day)
    df.set_index(['day'], inplace=True)
    df.index.name=''
    if (end_date!='') & (frequency in ['240m','1200m','7200m']): 
        return df[df.index <= end_date][-mcount:]
    return df


def _get_price(code, end_date='',count=10, frequency='1d', fields=[]):        
    xcode= code.replace('.XSHG','').replace('.XSHE','')                      #证券代码编码兼容处理 
    xcode='sh'+xcode if ('XSHG' in code)  else  'sz'+xcode  if ('XSHE' in code)  else code     
    if  frequency in ['1d','1w','1M']:   #1d日线  1w周线  1M月线
        try:    return _get_price_sina( xcode, end_date=end_date,count=count,frequency=frequency)   #主力
        except: return _get_price_day_tx(xcode,end_date=end_date,count=count,frequency=frequency)   #备用                    
    if  frequency in ['1m','5m','15m','30m','60m']:  #分钟线 ,1m只有腾讯接口  5分钟5m   60分钟60m
        if frequency in '1m': return _get_price_min_tx(xcode,end_date=end_date,count=count,frequency=frequency)
        try:    return _get_price_sina(  xcode,end_date=end_date,count=count,frequency=frequency)   #主力   
        except: return _get_price_min_tx(xcode,end_date=end_date,count=count,frequency=frequency)   #备用


def _load_all_stock_data() -> bool:
    global _stock_data_cache
    if all(key in _stock_data_cache and _stock_data_cache[key] is not None for key in STOCK_DATA_KEYS):
        _log_debug("--- [Cache] 所有股票映射数据已加载。 ---")
        return True
    _log_debug(f"--- [Cache] 正在从 Pickle 文件 '{LOCAL_PICKLE_FILE}' 加载所有股票数据... ---")
    if not os.path.exists(LOCAL_PICKLE_FILE):
        _log_debug(f"--- [Cache] 错误: Pickle 文件 '{LOCAL_PICKLE_FILE}' 未找到。 ---")
        return False
    try:
        with open(LOCAL_PICKLE_FILE, 'rb') as f:
            data_archive = pickle.load(f)
        for key_alias, (archive_key, name_col, code_col) in STOCK_DATA_KEYS.items():
            if _stock_data_cache.get(key_alias) is None: 
                if archive_key in data_archive:
                    df = data_archive[archive_key]
                    if name_col not in df.columns:
                        _log_debug(f"--- [Cache] 严重错误: '{archive_key}' 中缺少 'STOCK_DATA_KEYS' 定义的名称列: '{name_col}'")
                        _stock_data_cache[key_alias] = None 
                        continue 
                    if code_col not in df.columns:
                        _log_debug(f"--- [Cache] 严重错误: '{archive_key}' 中缺少 'STOCK_DATA_KEYS' 定义的代码列: '{code_col}'")
                        _stock_data_cache[key_alias] = None 
                        continue 
                    df['normalized_name'] = df[name_col].astype(str).apply(_normalize_stock_name)
                    _stock_data_cache[key_alias] = df
                else:
                    _log_debug(f"--- [Cache] 警告: Pickle 文件中缺少预期的键: '{archive_key}'。 ---")
                    _stock_data_cache[key_alias] = None
        return True
    except Exception as e:
        _log_debug(f"--- [Cache] 错误: 加载 Pickle 文件失败: {e} ---")
        return False


def _normalize_stock_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = name.lower().strip()
    name = re.sub(r'[^\w\u4e00-\u9fa5]', '', name)
    return name


def _fetch_a_history(symbol: str, adjust: str, start_date: str = "19700101", end_date: str = "22220101") -> Optional[pd.DataFrame]:
    global _a_history_cache
    cache_key = (symbol, adjust, start_date, end_date)
    if cache_key in _a_history_cache:
        _log_debug(f"--- [A股历史] 缓存命中: {symbol} ({adjust}) ---")
        return _a_history_cache[cache_key]
    df_hist, source = None, "未知"
    if symbol.startswith('bj'):
        _log_debug(f"--- [A股历史] 检测到北京 (BJ) 股票: {symbol}。正在使用 'ak.stock_bj_a_hist'... ---")
        try:
            symbol_no_prefix = symbol.replace("bj", "")
            df_raw = ak.stock_bj_a_hist(symbol=symbol_no_prefix, adjust=adjust)
            if df_raw is not None and not df_raw.empty:
                source = "Akshare/Beijing"
                df_hist = df_raw.copy()
        except Exception as e:
            _log_debug(f"--- [A股历史] 错误: 'ak.stock_bj_a_hist' 调用失败: {e}")
    else: 
        symbol_no_prefix = symbol.replace("sh", "").replace("sz", "")
        try:
            _log_debug(f"  -> 正在尝试从 [主源-Akshare/Eastmoney] 获取 '{symbol_no_prefix}' (adjust={adjust}) 的历史数据...")
            df_raw = ak.stock_zh_a_hist(
                symbol=symbol_no_prefix, period="daily",
                start_date=start_date.replace("-", ""), 
                end_date=end_date.replace("-", ""),   
                adjust=adjust
            )
            if df_raw is not None and not df_raw.empty:
                source = "Akshare/Eastmoney"
                df_hist = df_raw.copy()
        except Exception as e:
            _log_debug(f"  -> 从 [主源-Akshare/Eastmoney] 获取历史数据失败: {e}。将尝试备用源 1。")
        if df_hist is None and start_date == "19700101":
            _log_debug("--- [A股历史] 主源失败，正在回退到 [Ashare] (Sina/Tencent)... ---")
            try:
                _log_debug(f"  -> 正在尝试从 [备用源 1-Ashare/Sina] 获取 '{symbol}'...")
                df_raw = _get_price_sina(symbol, end_date=end_date, count=99999, frequency='1d')
                if df_raw is not None and not df_raw.empty:
                    source = "Ashare/Sina"
                    df_raw.index.name = '日期' 
                    df_hist = df_raw.reset_index() 
                else:
                    raise ValueError("Sina 返回为空")
            except Exception as e_sina:
                _log_debug(f"  -> 从 [备用源 1-Ashare/Sina] 失败: {e_sina}。将尝试备用源 2。")
                try:
                    _log_debug(f"  -> 正在尝试从 [备用源 2-Ashare/Tencent] 获取 '{symbol}' (adjust={adjust})...")
                    df_raw = _get_price_day_tx(symbol, end_date=end_date, count=99999, frequency='1d', adjust=adjust)
                    if df_raw is not None and not df_raw.empty:
                        source = "Ashare/Tencent"
                        df_raw.index.name = '日期'
                        df_hist = df_raw.reset_index()
                    else:
                        raise ValueError("Tencent 返回为空")
                except Exception as e_tx:
                    _log_debug(f"  -> 从 [备用源 2-Ashare/Tencent] 失败: {e_tx}。")
    if df_hist is None:
        _log_debug(f"--- [A股历史] 错误: 所有可用数据源均未能获取 '{symbol}' 的数据。 ---")
        return None
    _log_debug(f"--- [A股历史] 成功从 [{source}] 获取数据。正在进行标准化处理... ---")
    df_hist.rename(columns={
        'date': '日期', 
        'open': '开盘', 'close': '收盘', 'high': '最高', 'low': '最低',
        'volume': '成交量', 'amount': '成交额'
    }, inplace=True, errors='ignore')
    if source in ["Akshare/Eastmoney", "Akshare/Beijing"]:
        if '成交量' in df_hist.columns:
            df_hist['成交量'] = df_hist['成交量'] * 100
    if '日期' not in df_hist.columns:
         _log_debug(f"--- [A股历史] 严重错误: 标准化后, '{source}' 的数据仍缺少 '日期' 列。")
         return None
    df_hist['日期'] = pd.to_datetime(df_hist['日期']).dt.strftime('%Y-%m-%d')
    df_hist.sort_values(by='日期', ascending=False, inplace=True)
    df_hist_final = df_hist.reset_index(drop=True)
    if source == "Akshare/Eastmoney":
        _a_history_cache[cache_key] = df_hist_final
    return df_hist_final


def _fetch_a_spot_data() -> Optional[pd.DataFrame]:
    global _a_spot_cache, _a_spot_cache_time
    if _a_spot_cache is not None and (datetime.now() - _a_spot_cache_time).total_seconds() < 600:
        _log_debug("--- [A股实时] 缓存命中 (10分钟内)，跳过 API 调用。 ---")
        return _a_spot_cache
    _log_debug("--- [A股实时] 正在通过 ak.stock_zh_a_spot() 获取最新实时数据... ---")
    try:
        time.sleep(30)
        df = ak.stock_zh_a_spot() 
        if df is None or df.empty:
            _log_debug("--- [A股实时] 错误: API未返回任何实时数据。 ---")
            return None
        df['normalized_name'] = df['名称'].astype(str).apply(_normalize_stock_name)
        _a_spot_cache = df
        _a_spot_cache_time = datetime.now()
        _log_debug(f"--- [A股实时] 成功获取 {len(df)} 条数据并已缓存。 ---")
        return df
    except Exception as e:
        _log_debug(f"--- [A股实时] 错误: 从 ak.stock_zh_a_spot 获取数据失败: {e} ---")
        return None


def _fetch_a_realtime_hybrid(
    resolved_symbol: str, 
    resolved_ts_code: str,
    target_col: str 
) -> Tuple[Optional[pd.Series], str]:
    _log_debug(f"--- [A股实时] 正在尝试 [P1 主源 Ashare] _get_price(code={resolved_symbol}, freq=1d)... ---")
    try:
        df_ashare = _get_price(code=resolved_symbol, frequency='1d', count=1) 
        if df_ashare is not None and not df_ashare.empty:
            realtime_row = df_ashare.iloc[-1].copy() 
            realtime_row['日期'] = realtime_row.name.strftime('%Y-%m-%d %H:%M:%S')
            realtime_row['开盘'] = realtime_row['open']
            realtime_row['收盘'] = realtime_row['close']
            realtime_row['最高'] = realtime_row['high']
            realtime_row['最低'] = realtime_row['low']
            realtime_row['成交量'] = realtime_row['volume']
            if target_col in realtime_row:
                return realtime_row, "Ashare (Sina/Tencent)"
            else:
                _log_debug(f"  -> [Ashare] 成功, 但缺少 '{target_col}' 列。正在回退...")
        else:
            _log_debug(f"  -> [Ashare] 失败: API 返回为空。")
    except Exception as e:
        _log_debug(f"  -> [Ashare] 失败: {e}")
    _log_debug(f"--- [A股实时] [P1 Ashare] 失败或缺少数据。正在回退到 [P2 备用源 Akshare]... ---")
    try:
        df_akshare_spot = _fetch_a_spot_data() 
        if df_akshare_spot is not None:
            match = df_akshare_spot[df_akshare_spot['代码'] == resolved_symbol]
            if not match.empty:
                realtime_row = match.iloc[0].copy()
                # [标准化] Akshare -> 中文
                realtime_row['日期'] = datetime.now().strftime('%Y-%m-%d')
                realtime_row['开盘'] = realtime_row['今开']
                realtime_row['收盘'] = realtime_row['最新价']
                realtime_row['最高'] = realtime_row['最高']
                realtime_row['最低'] = realtime_row['最低']
                realtime_row['成交量'] = realtime_row['成交量']
                realtime_row['成交额'] = realtime_row['成交额'] # <-- Akshare 有 '成交额'
                if target_col in realtime_row:
                    return realtime_row, "Akshare (Spot)"
                else:
                    _log_debug(f"  -> [Akshare Spot] 成功, 但缺少 '{target_col}' 列。正在回退...")
    except Exception as e:
        _log_debug(f"  -> [Akshare Spot] 失败: {e}")
    _log_debug(f"--- [A股实时] 错误: 所有 2 个实时数据源均失败, 或都缺少 '{target_col}'。 ---")
    return None, "All Failed"


def _fetch_a_history_hybrid(
    resolved_symbol: str, 
    resolved_ts_code: str, 
    resolved_ak_code: str,
    adjust: str,
    start_date: str,
    end_date: str
) -> Tuple[Optional[pd.DataFrame], str]:
    df_hist = None
    source = "Unknown"
    _log_debug(f"--- [A股历史] 正在使用 Akshare/Ashare 四核数据源... ---")
    if df_hist is None:
        try:
            df_hist = _fetch_a_history(
                symbol=resolved_symbol, 
                adjust=adjust,
                start_date=start_date,
                end_date=end_date
            ) 
            source = "Akshare/Ashare (Four-Core)"
        except Exception as e:
            _log_debug(f"  -> [四核 _fetch_a_history] 失败: {e}")
            df_hist = None
    if df_hist is None: 
        _log_debug(f"--- [A股历史] 错误: 数据源 (Akshare/Ashare) 失败。 ---")
        return None, "All Failed"
    return df_hist, source


def _fetch_us_spot_data() -> Optional[pd.DataFrame]:
    global _us_spot_cache, _us_spot_cache_time
    if _us_spot_cache is not None and (datetime.now() - _us_spot_cache_time).total_seconds() < US_SPOT_CACHE_EXPIRY_SECONDS:
        _log_debug("--- [美股实时] 缓存命中 (10分钟内)，跳过 API 调用。 ---")
        return _us_spot_cache
    _log_debug("--- [美股实时] 正在通过 ak.stock_us_spot() 获取最新实时数据 (全量)... ---")
    try:
        time.sleep(30) 
        df = ak.stock_us_spot() 
        if df is None or df.empty:
            _log_debug("--- [美股实时] 错误: API未返回任何实时数据。 ---")
            return None
        df['normalized_name'] = (df['name'].astype(str).apply(_normalize_stock_name) + " " + df['cname'].astype(str).apply(_normalize_stock_name))
        df['symbol'] = df['symbol'].astype(str).str.upper() # 确保 symbol 大写
        _us_spot_cache = df
        _us_spot_cache_time = datetime.now()
        _log_debug(f"--- [美股实时] 成功获取 {len(df)} 条数据并已缓存。 ---")
        return df
    except Exception as e:
        _log_debug(f"--- [美股实时] 错误: 从 ak.stock_us_spot 获取数据失败: {e} ---")
        return None


def _fetch_hk_spot_data() -> Optional[pd.DataFrame]:
    global _hk_spot_cache, _hk_spot_cache_time
    if _hk_spot_cache is not None and (datetime.now() - _hk_spot_cache_time).total_seconds() < HK_SPOT_CACHE_EXPIRY_SECONDS:
        _log_debug("--- [港股实时] 缓存命中 (10分钟内)，跳过 API 调用。 ---")
        return _hk_spot_cache
    _log_debug(f"--- [港股实时] 正在通过 ak.stock_hk_spot() 获取最新实时数据 (全量)... ---")
    for attempt in range(MAX_API_RETRIES):
        try:
            _log_debug(f"  -> 尝试 {attempt + 1}/{MAX_API_RETRIES}...")
            time.sleep(10 * (attempt + 1)) 
            df = ak.stock_hk_spot()
            if df is not None and not df.empty:
                _log_debug(f"--- [港股实时] 成功获取数据 (尝试 {attempt + 1})。 ---")
                df['normalized_name'] = (
                    df['中文名称'].astype(str).apply(_normalize_stock_name) + " " +
                    df['英文名称'].astype(str).apply(_normalize_stock_name)
                )
                df['代码'] = df['代码'].astype(str).str.strip().str.zfill(5)
                _hk_spot_cache = df
                _hk_spot_cache_time = datetime.now()
                return df
            _log_debug(f"  -> 尝试 {attempt + 1} 失败: API返回空数据。")
        except Exception as e:
            _log_debug(f"  -> ❌ 尝试 {attempt + 1} 失败: {type(e).__name__} - {e}")
        if attempt < MAX_API_RETRIES - 1:
            _log_debug(f"  -> {RETRY_SLEEP_SECONDS} 秒后重试...")
            time.sleep(RETRY_SLEEP_SECONDS)
    _log_debug(f"--- [港股实时] ❌ 错误: 经过 {MAX_API_RETRIES} 次尝试后仍无法获取数据。 ---")
    return None


def _fetch_hk_history(symbol: str, adjust: str) -> Optional[pd.DataFrame]:
    """
    获取港股历史数据，并尝试使用两个数据源。
    """
    df_hist, source = None, "未知"
    try:
        _log_debug(f"  -> 正在尝试从 [主源-新浪] 获取 '{symbol}' 的历史数据...")
        time.sleep(30) 
        df_raw = ak.stock_hk_daily(symbol=symbol, adjust=adjust)
        if df_raw is not None and not df_raw.empty:
            source = "新浪"
            df_hist = df_raw.rename(columns={
                'date': '日期', 'open': '开盘', 'high': '最高', 'low': '最低',
                'close': '收盘', 'volume': '成交量'
            })
    except Exception as e:
        _log_debug(f"  -> 从新浪获取历史数据失败: {e}。将尝试备用源。")
    
    if df_hist is None:
        _log_debug(f"  -> (暂停 120 秒后尝试备用源...)")
        time.sleep(120) 
        try:
            _log_debug(f"  -> 正在尝试从 [备用源-东财] 获取 '{symbol}' 的历史数据...")
            df_raw = ak.stock_hk_hist(symbol=symbol, adjust=adjust)
            if df_raw is not None and not df_raw.empty:
                source = "东方财富"
                df_hist = df_raw
        except Exception as e:
            _log_debug(f"  -> 从备用源东方财富获取历史数据也失败: {e}")
            
    if df_hist is None: return None
    
    _log_debug(f"--- 成功从 [{source}] 获取数据。正在进行标准化处理... ---")
    df_hist['日期'] = pd.to_datetime(df_hist['日期']).dt.strftime('%Y-%m-%d')
    df_hist.sort_values(by='日期', ascending=False, inplace=True)
    return df_hist.reset_index(drop=True)


def _fail_minute_spread(error_msg: str) -> Dict[str, Any]:
    """
    [辅助函数] 确保 calculate_futures_minute_spread 
    """
    _log_debug(f"[Debug] [calculate_futures_minute_spread] 失败: {error_msg}")
    _log_debug(f"[Debug] [calculate_futures_minute_spread] 正在返回哨兵值 0.0 以防止 solve() 崩溃。")
    return {
        'max_spread': {
            'value': 0.0, 
            'date': "1970-01-01 00:00:00", 
            'error': error_msg
        },
        'min_spread': { 
            'value': 0.0,
            'date': "1970-01-01 00:00:00",
            'error': error_msg
        }
    }


def _normalize_name(s: str) -> str:
    """标准化指数名称 (移除空格)"""
    if not isinstance(s, str): return ""
    return s.lower().replace(" ", "")


# Now define ALIAS_TO_STANDARD_NAME_MAP after _normalize_name is defined
ALIAS_TO_STANDARD_NAME_MAP = {
    _normalize_name("S&P 500"): "标普500",
    _normalize_name("spx"): "标普500",
    _normalize_name("dow jones"): "道琼斯工业平均指数",
    _normalize_name("dow"): "道琼斯工业平均指数",
    _normalize_name("djia"): "道琼斯工业平均指数",
    _normalize_name("nasdaq"): "纳斯达克综合指数",
    _normalize_name("ixic"): "纳斯达克综合指数",
    _normalize_name("hsi"): "恒生指数",
    _normalize_name("台湾加权指数"): "台湾加权",
    _normalize_name("长三角指数"): "长三角",
    _normalize_name("雅加达综合股价指数"): "印尼雅加达综合",
    _normalize_name("jakarta stock exchange composite"): "印尼雅加达综合",
    _normalize_name("idx composite"): "印尼雅加达综合",
    _normalize_name("jkse"): "印尼雅加达综合",
    _normalize_name('Nikkei 225'): "N225",
    _normalize_name("S&P/ASX 200"): "AS51",
    _normalize_name("德国DAX指数"): "德国DAX30",
    _normalize_name("DAX Index"): '德国DAX30',
    _normalize_name("SMI"): 'SSMI',
    _normalize_name("Swiss Market Index"): "SSMI"
}


def _fetch_index_spot_api(market_key: str, api_func: callable) -> Optional[pd.DataFrame]:
    if market_key in _index_spot_caches and (datetime.now() - _index_spot_cache_times.get(market_key, datetime.min)).total_seconds() < INDEX_SPOT_CACHE_EXPIRY_SECONDS:
        _log_debug(f"--- [实时指数] 缓存命中 ({market_key})，跳过 API 调用。 ---")
        return _index_spot_caches[market_key]
    _log_debug(f"--- [实时指数] 正在通过 API ({market_key}) 获取最新数据... ---")
    try:
        time.sleep(30) 
        df = api_func() 
        if df is None or df.empty:
            _log_debug(f"--- [实时指数] 错误: {market_key} API未返回任何数据。 ---")
            return None
        if market_key == 'us_index':
            if 'symbol' in df.columns:
                df['代码'] = df['symbol'].astype(str).str.upper() # 将 symbol 映射到 '代码'
        _index_spot_caches[market_key] = df
        _index_spot_cache_times[market_key] = datetime.now()
        _log_debug(f"--- [实时指数] 成功获取 {len(df)} 条 {market_key} 数据并已缓存。 ---")
        return df
    except Exception as e:
        _log_debug(f"--- [实时指数] 错误: {market_key} API 调用失败: {e} ---")
        return None


def _load_all_index_data() -> bool:
    global _index_data_cache
    # 修复后的代码
    # 检查："是否 INDEX_DATA_KEYS 中的所有键都存在于缓存中，并且它们的值都不是 None？"
    if all(key in _index_data_cache and _index_data_cache[key] is not None for key in INDEX_DATA_KEYS):
        _log_debug("--- [Cache] 所有指数映射数据已加载。 ---")
        return True
    _log_debug(f"--- [Cache] 正在从 Pickle 文件 '{LOCAL_PICKLE_FILE}' 加载所有指数数据... ---")
    if not os.path.exists(LOCAL_PICKLE_FILE):
        _log_debug(f"--- [Cache] 错误: Pickle 文件 '{LOCAL_PICKLE_FILE}' 未找到。 ---")
        return False
    try:
        with open(LOCAL_PICKLE_FILE, 'rb') as f:
            data_archive = pickle.load(f)
        success = True
        for key_alias, (archive_key, name_col, code_col) in INDEX_DATA_KEYS.items():
            if archive_key in data_archive:
                df = data_archive[archive_key]
                df['normalized_name'] = df[name_col].astype(str).str.strip().apply(_normalize_name)
                df[code_col] = df[code_col].astype(str).str.strip().str.lower()
                _index_data_cache[key_alias] = df
            else:
                _log_debug(f"--- [Cache] 警告: Pickle 文件中缺少预期的键: '{archive_key}'。 ---")
                _index_data_cache[key_alias] = None
                success = False 
        return success
    except Exception as e:
        _log_debug(f"--- [Cache] 错误: 加载 Pickle 文件失败: {e} ---")
        return False


def _find_index_code_and_market(identifier: str, market_hint: Optional[str] = None) -> Optional[Tuple[str, str, str]]:
    global _index_data_cache
    _log_debug(f"--- [辅助函数] 正在为 '{identifier}' 查找信息 (市场提示: {market_hint})... ---")
    if not _load_all_index_data():
        _log_debug("--- [辅助函数] 查找失败。无法加载指数数据归档。 ---")
        return None
    US_INDEX_MAP = {
        ".IXIC": ("纳斯达克综合指数", ".IXIC", "IXIC"),
        "IXIC": ("纳斯达克综合指数", ".IXIC", "IXIC"),
        ".DJI": ("道琼斯工业平均指数", ".DJI", "DJI"),
        "DJI": ("道琼斯工业平均指数", ".DJI", "DJI"),
        ".INX": ("标普500", ".INX", "INX"),
        "INX": ("标普500", ".INX", "INX"),
        ".NDX": ("纳斯达克100", ".NDX", "NDX"),
        "NDX": ("纳斯达克100", ".NDX", "NDX"),
    }
    search_key_upper = identifier.upper().replace(".", "")
    if search_key_upper in US_INDEX_MAP:
        name, code, _ = US_INDEX_MAP[search_key_upper]
        _log_debug(f"--- [辅助函数] 识别为US指数 '{name}' (代码: {code})")
        return code, name, 'us_index'
    search_list = []
    if market_hint:
        hint_key = f"{market_hint.lower()}_index"
        sorted_keys = sorted(INDEX_DATA_KEYS.keys(), key=lambda x: x != hint_key)
        search_list = [(key, INDEX_DATA_KEYS[key]) for key in sorted_keys]
    else:
        search_list = list(INDEX_DATA_KEYS.items())
    normalized_input = _normalize_name(identifier)
    standard_name = ALIAS_TO_STANDARD_NAME_MAP.get(normalized_input)
    search_target_norm = _normalize_name(standard_name) if standard_name else normalized_input
    for market_key, (archive_key, name_col, code_col) in search_list:
        df = _index_data_cache.get(market_key) 
        if df is None or df.empty: continue
        code_search_input = identifier.lower()
        df_codes_as_string = df[code_col] 
        code_match = df[df_codes_as_string == code_search_input]
        if not code_match.empty:
            row = code_match.iloc[0]
            _log_debug(f"--- [辅助函数] 通过代码 '{identifier}' 在 '{market_key}' 中找到 '{row[name_col]}'")
            return str(row[code_col]), str(row[name_col]), market_key
        normalized_df_names = df['normalized_name'] # 已在加载时创建
        exact_match = df[normalized_df_names == search_target_norm]
        if not exact_match.empty:
            row = exact_match.iloc[0]
            _log_debug(f"--- [辅助函数] 通过名称 '{identifier}' 在 '{market_key}' 中找到 '{row[name_col]}'")
            return str(row[code_col]), str(row[name_col]), market_key
    for market_key, (archive_key, name_col, code_col) in search_list:
        df = _index_data_cache.get(market_key)
        if df is None or df.empty: continue
        normalized_df_names = df['normalized_name'] # 已在加载时创建
        fuzzy_target = _normalize_name(identifier)
        if len(fuzzy_target) < 3: continue 
        contain_match = df[normalized_df_names.str.contains(fuzzy_target, na=False)]
        if not contain_match.empty:
            row = contain_match.iloc[0]
            _log_debug(f"--- [辅助函数] 通过名称 (模糊匹配) '{identifier}' 在 '{market_key}' 中找到 '{row[name_col]}'")
            return str(row[code_col]), str(row[name_col]), market_key
    _log_debug(f"--- [辅助函数] 未能找到 '{identifier}' 对应的任何信息。 ---")
    return None


def _parse_index_price_from_output(output: Any) -> Tuple[Optional[float], Optional[str]]:
    if not isinstance(output, dict):
        _log_debug(f"  -> [指数解析器] 失败: 底层工具返回的不是字典: {output}")
        return None, None
    price = output.get('value')
    date_str = output.get('datetime', output.get('date'))
    if price is None:
        _log_debug(f"  -> [指数解析器] 失败: 未能在 {output} 中找到 'value' 键。")
        return None, date_str
    if date_str is None:
        _log_debug(f"  -> [指数解析器] 警告: 未能在 {output} 中找到 'datetime' 或 'date' 键。")
    try:
        if isinstance(price, str):
            _log_debug(f"  -> [指数解析器] 失败: 'value' 是一个错误字符串: {price}")
            return None, date_str
        return float(price), date_str
    except (ValueError, TypeError):
        _log_debug(f"  -> [指数解析器] 失败: 'value' 不是一个有效的数字: {price}")
        return None, date_str


def _parse_price_from_tool_output(output: str) -> Optional[float]:
    """辅助函数：从 '值 (数据日期: ...)' 格式的字符串中安全地提取价格浮点数。"""
    if not isinstance(output, str):
        return None
    match = re.match(r'^(-?\d+\.?\d*)', output)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, TypeError):
            return None
    return None


def _parse_price_and_date_from_output(
    price_output: Dict[str, Any]
) -> Tuple[Optional[float], Optional[str]]:
    if not isinstance(price_output, dict):
        _log_debug(f"  -> [解析器] 失败: 底层工具返回的不是字典: {price_output}")
        return None, None
    value = None
    raw_value = None 
    try:
        if 'requested_item' in price_output and isinstance(price_output['requested_item'], dict):
            raw_value = price_output['requested_item'].get('value')
        elif 'value' in price_output:
            raw_value = price_output.get('value')
        elif 'result' in price_output:
            raw_value = price_output.get('result')
        else:
            _log_debug(f"  -> [解析器] 失败: 找不到 'requested_item', 'value', 或 'result' 键。")
            return None, None
        if raw_value is None:
            _log_debug(f"  -> [解析器] 失败: 'value' 键为 None。")
            return None, None
        value = float(raw_value)
    except (ValueError, TypeError) as e:
        _log_debug(f"  -> [解析器] 失败: 'value' 无法转换为 float: {e}。原始值: {raw_value}")
        return None, None
    except Exception as e_ex:
        _log_debug(f"  -> [解析器] 发生意外错误: {e_ex}")
        return None, None
    date_str = price_output.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return value, str(date_str)


def _parse_chinese_number_unit(value_str: str) -> Optional[float]:
    if not isinstance(value_str, str): return value_str
    try:
        value_str = value_str.strip()
        if '亿' in value_str: return float(value_str.replace('亿', '')) * 1e8
        elif '万' in value_str: return float(value_str.replace('万', '')) * 1e4
        elif '%' in value_str: return float(value_str.replace('%', '')) / 100
        else: return float(value_str)
    except (ValueError, TypeError): return None


def _fetch_single_index_history_range(
    identifier: str, 
    start_date: str, 
    end_date: str
) -> Union[pd.DataFrame, str]:
    """
    获取单个指数在指定时间段内的全部历史数据DataFrame。
    """
    _log_debug(f"--- [数据获取子任务] 正在获取 '{identifier}' 从 {start_date} 到 {end_date} 的数据... ---")
    entity_info = _find_index_code_and_market(identifier=identifier)
    if not entity_info: return f"实体链接失败: '{identifier}'"
    code_for_api, name_for_api, identified_market = entity_info
    market_for_api = identified_market.replace("_index", "")
    all_history_df = None
    api_sources = []
    start_date_fmt = start_date.replace('-', '')
    end_date_fmt = end_date.replace('-', '')
    if market_for_api == 'a':
        api_sources = [
            lambda: ak.index_zh_a_hist(symbol=code_for_api[2:], period="daily", start_date=start_date_fmt, end_date=end_date_fmt),
            lambda: ak.stock_zh_index_daily(symbol=code_for_api)
        ]
    elif market_for_api == 'hk':
        api_sources = [lambda: ak.stock_hk_index_daily_sina(symbol=code_for_api)]
    elif market_for_api == 'us':
        us_symbol = f".{code_for_api.upper().lstrip('.')}"
        api_sources = [lambda: ak.index_us_stock_sina(symbol=us_symbol)]
    elif market_for_api == 'global':
        api_sources = [lambda: ak.index_global_hist_em(symbol=name_for_api, start_date=start_date_fmt, end_date=end_date_fmt)]
        US_INDEX_IDENTIFIERS = ['IXIC', 'DJI', 'SPX', '纳斯达克', '道琼斯', '标普']
        if any(us_id in code_for_api.upper() or us_id in name_for_api for us_id in US_INDEX_IDENTIFIERS):
            us_symbol = f".{code_for_api.upper().lstrip('.')}"
            api_sources.insert(0, lambda: ak.index_us_stock_sina(symbol=us_symbol))
    for fetch_func in api_sources:
        try:
            temp_df = fetch_func()
            if temp_df is not None and not temp_df.empty:
                all_history_df = temp_df
                break
        except Exception as e:
            _log_debug(f"--- [数据获取子任务] 接口调用失败: {e} ---")
            continue
    if all_history_df is None or all_history_df.empty:
        return f"所有接口均未能获取到 '{identifier}' 的数据。"
    all_history_df.rename(columns=_COLUMN_MAP_AK_TO_STD, inplace=True, errors='ignore')
    if 'date' not in all_history_df.columns:
        return f"获取到的 '{identifier}' 数据缺少'date'列。"
    all_history_df['date'] = pd.to_datetime(all_history_df['date'])
    mask = (all_history_df['date'] >= start_date) & (all_history_df['date'] <= end_date)
    filtered_df = all_history_df.loc[mask].copy()
    filtered_df['identifier'] = name_for_api 
    return filtered_df


def _format_date(stat_time_obj):
    s = str(stat_time_obj)
    parts = s.split('.')
    if len(parts) == 2:
        year = parts[0]
        month = int(parts[1])
        return f"{year}-{month:02d}"
    return s


@lru_cache(maxsize=1)
def _get_and_clean_gold_forex_data() -> Union[pd.DataFrame, str]:
    df = pd.DataFrame()
    try:
        _log_debug("--- [数据接口] 正在尝试主数据源 (新浪财经)... ---")
        df_sina = ak.macro_china_foreign_exchange_gold()
        df_sina['统计时间'] = df_sina['统计时间'].apply(_format_date)
        df = df_sina[['统计时间', '黄金储备', '国家外汇储备']]
        _log_debug("--- [数据接口] 主数据源 (新浪财经) 获取成功。 ---")
    except Exception as e_sina:
        _log_debug(f"--- [数据接口] 主数据源 (新浪财经) 获取失败: {e_sina} ---")
        _log_debug("--- [数据接口] 正在尝试切换到您指定的备用数据源 (东方财富)... ---")
        try:
            df_em = ak.macro_china_fx_gold()
            df_em = df_em[['月份', '黄金储备-数值', '国家外汇储备-数值']]
            df_em.rename(columns={
                '月份': '统计时间',
                '黄金储备-数值': '黄金储备',
                '国家外汇储备-数值': '国家外汇储备'
            }, inplace=True)
            df_em['统计时间'] = df_em['统计时间'].str.replace('年', '-').str.replace('月份', '')
            df = df_em
            _log_debug("--- [数据接口] 备用数据源 (东方财富) 获取成功。 ---")
        except Exception as e_em:
            error_message = f"错误：备用数据源 (东方财富) 也获取失败: {e_em} ---"
            _log_debug(f"--- [数据接口] 备用数据源 (东方财富) 也获取失败: {e_em} ---")
            return error_message
    if not df.empty:
        df.dropna(inplace=True)
        df.sort_values('统计时间', inplace=True)
        return df
    error_message = "错误：数据源调用成功，但未返回任何有效数据。"
    _log_debug(f"--- [数据接口] {error_message} ---")
    return error_message


@lru_cache(maxsize=1)
def _get_and_clean_m2_data() -> Union[pd.DataFrame, str]:
    """
    [内部函数] 获取并预处理中国M2货币供应年率数据。
    [已修复] 仅使用 akshare 实时接口获取数据，移除所有本地 CSV 回退逻辑。
    """
    df = pd.DataFrame()
    
    try:
        _log_debug("--- [数据接口] 正在尝试主数据源 (akshare.macro_china_m2_yearly)... ---")
        
        # 1. 调用 API 获取数据
        df_ak = ak.macro_china_m2_yearly() 
        
        # 2. 标准化和精简
        df_ak.rename(columns={'日期': 'date', '今值': 'value'}, inplace=True)
        
        # 确保 date 列存在且可解析，以便后续操作
        if 'date' not in df_ak.columns or 'value' not in df_ak.columns:
             error_message = "错误：API 返回数据结构不匹配，缺少 '日期' 或 '今值' 列。"
             _log_debug(f"--- [数据接口] {error_message} ---")
             return error_message
             
        df_ak['date'] = pd.to_datetime(df_ak['date']).dt.strftime('%Y-%m')
        df = df_ak[['date', 'value']]
        
        _log_debug("--- [数据接口] 主数据源 (akshare接口) 获取成功。 ---")

    except Exception as e:
        error_message = f"错误：数据源调用失败 (akshare.macro_china_m2_yearly): {e}"
        _log_debug(f"--- [数据接口] {error_message} ---")
        return error_message
        
    # 3. 清洗和返回
    if not df.empty:
        df.dropna(subset=['value'], inplace=True)
        df.drop_duplicates(subset=['date'], keep='first', inplace=True)
        df.sort_values('date', inplace=True, ignore_index=True)
        
        if df.empty:
            error_message = "错误：数据源获取成功，但清洗后(去重或去空值)未剩任何有效数据。"
            _log_debug(f"--- [数据接口] {error_message} ---")
            return error_message
            
        return df # 返回 DataFrame
        
    # 如果 df 为空但没有抛出异常
    error_message = "错误：数据源调用成功，但未返回任何有效数据。"
    _log_debug(f"--- [数据接口] {error_message} ---")
    return error_message


@lru_cache(maxsize=1)
def _get_and_clean_currency_data() -> Union[pd.DataFrame, str]: 
    """
    [辅助函数] 获取并预处理人民币汇率中间价数据。
    使用缓存避免在单次运行中重复调用API。
    """
    _log_debug("--- [数据接口] 正在调用 'ak.currency_boc_safe'... ---")
    try:
        df = ak.currency_boc_safe()
        if df.empty:
            error_message = "错误：API (ak.currency_boc_safe) 调用成功，但未返回任何数据。"
            _log_debug(f"--- [数据接口] {error_message} ---")
            return error_message
        df['日期'] = pd.to_datetime(df['日期'])
        df.set_index('日期', inplace=True)
        return df
    except Exception as e:
        error_message = f"错误：调用API (ak.currency_boc_safe) 或处理数据时失败: {e}"
        _log_debug(f"--- [数据接口] {error_message} ---")
        return error_message 


@lru_cache(maxsize=1)
def _get_futures_symbol_map() -> Union[Dict[str, str], str]: # <-- 2. 更新了返回类型
    """
    [辅助函数] 获取新浪财经的主力连续合约品种列表，并创建一个名称到代码的映射。
    使用缓存避免重复调用API。
    """
    _log_debug("--- [数据接口] 正在调用 'ak.futures_display_main_sina' 获取期货品种列表... ---")
    try:
        df = ak.futures_display_main_sina()
        if df.empty:
            error_message = "错误：API (ak.futures_display_main_sina) 调用成功，但未返回任何期货品种数据。"
            _log_debug(f"--- [数据接口] {error_message} ---")
            return error_message
        name_to_symbol = {row['name'].replace('连续', ''): row['symbol'] for _, row in df.iterrows()}
        symbol_to_symbol = {row['symbol'].lower(): row['symbol'] for _, row in df.iterrows()}
        name_to_symbol.update(symbol_to_symbol)
        if not name_to_symbol:
            error_message = "错误：成功获取期货数据，但在创建映射时失败（结果为空）。"
            _log_debug(f"--- [数据接口] {error_message} ---")
            return error_message
        return name_to_symbol
    except Exception as e:
        error_message = f"错误：获取期货品种列表 (ak.futures_display_main_sina) 失败: {e}"
        _log_debug(f"--- [数据接口] {error_message} ---")
        return error_message 


@lru_cache(maxsize=1)
def _get_and_clean_ppi_data() -> Union[pd.DataFrame, str]: 
    """
    [内部函数] 获取并预处理中国PPI年率数据。
    使用缓存避免在单次运行中重复调用API。
    """
    _log_debug("--- [数据接口] 正在调用 'ak.macro_china_ppi_yearly'... ---")
    try:
        df = ak.macro_china_ppi_yearly()
        if df.empty:
            error_message = "错误：API (ak.macro_china_ppi_yearly) 调用成功，但未返回任何数据。"
            _log_debug(f"--- [数据接口] {error_message} ---")
            return error_message
        df.rename(columns={'日期': 'date', '今值': 'ppi_yoy'}, inplace=True)
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')
        df = df[['date', 'ppi_yoy']].dropna()
        if df.empty:
            error_message = "错误：PPI数据获取成功，但清洗后(去空值)未剩任何有效数据。"
            _log_debug(f"--- [数据接口] {error_message} ---")
            return error_message
        df.sort_values('date', inplace=True)
        return df
    except Exception as e:
        error_message = f"错误：调用API (ak.macro_china_ppi_yearly) 或处理数据时失败: {e}"
        _log_debug(f"--- [数据接口] {error_message} ---")
        return error_message 


@lru_cache(maxsize=1)
def _get_and_clean_lpr_data() -> Union[pd.DataFrame, str]:
    """
    [辅助函数] 获取并预处理中国LPR品种数据。
    使用缓存避免在单次运行中重复调用API。
    """
    _log_debug("--- [数据接口] 正在调用 'ak.macro_china_lpr'... ---")
    try:
        df = ak.macro_china_lpr()
        if df.empty:
            error_message = "错误：API (ak.macro_china_lpr) 调用成功，但未返回任何LPR数据。"
            _log_debug(f"--- [数据接口] {error_message} ---")
            return error_message
        df['TRADE_DATE'] = pd.to_datetime(df['TRADE_DATE'])
        df.set_index('TRADE_DATE', inplace=True)
        if df.index.empty:
            error_message = "错误：LPR数据获取成功，但处理后索引为空。"
            _log_debug(f"--- [数据接口] {error_message} ---")
            return error_message
        return df
    except Exception as e:
        error_message = f"错误：调用API (ak.macro_china_lpr) 或处理数据时失败: {e}"
        _log_debug(f"--- [数据接口] {error_message} ---")
        return error_message 


def _get_and_clean_forex_data(symbol: str) -> Union[pd.DataFrame, str]:
    """
    [辅助函数] 获取并缓存单个外汇品种的 *全部* 历史数据。
    """
    global _forex_hist_cache
    if symbol in _forex_hist_cache:
        _log_debug(f"--- [外汇缓存] 命中: 正在从缓存中读取 '{symbol}'... ---")
        return _forex_hist_cache[symbol]
    _log_debug(f"--- [外汇API] 缓存未命中: 正在调用 ak.forex_hist_em(symbol='{symbol}')... ---")
    try:
        df = ak.forex_hist_em(symbol=symbol)
        if df.empty:
            error_message = f"错误: API (ak.forex_hist_em) 为 '{symbol}' 返回了空数据。"
            _log_debug(f"--- [外汇API] {error_message} ---")
            return error_message
        df['日期'] = pd.to_datetime(df['日期'])
        df.set_index('日期', inplace=True)
        _forex_hist_cache[symbol] = df
        return df
    except Exception as e:
        error_message = f"错误: 调用API (ak.forex_hist_em) 或处理 '{symbol}' 数据时失败: {e}"
        _log_debug(f"--- [外汇API] {error_message} ---")
        return error_message


def _get_forex_history_em(
    symbols: List[str],
    start_date: str,
    end_date: str,
    columns_to_include: Optional[List[str]] = None
) -> Union[pd.DataFrame, str]:
    """
    从东方财富网获取一个或多个外汇品种在指定时间段内的历史行情数据。
    """
    if not isinstance(symbols, list) or not symbols:
        error_message = "错误：'symbols' 参数必须是一个非空的列表，例如 ['USDCNH']。"
        _log_debug(f"--- [外汇历史] {error_message} ---")
        return error_message
    VALID_COLUMNS = {'最新价', '涨跌额', '涨跌幅', '今开', '最高', '最低', '昨收'}
    if columns_to_include:
        invalid_columns = [col for col in columns_to_include if col not in VALID_COLUMNS]
        if invalid_columns:
            error_message = f"错误：请求了无效的列名 {invalid_columns}。有效列名包括: {list(VALID_COLUMNS)}"
            _log_debug(f"--- [外汇历史] {error_message} ---")
            return error_message
    else:
        columns_to_include = list(VALID_COLUMNS)
    try:
        pd.to_datetime(start_date)
        pd.to_datetime(end_date)
    except ValueError:
        error_message = "错误：日期格式不正确，请使用 'YYYY-MM-DD' 格式。"
        _log_debug(f"--- [外汇历史] {error_message} ---")
        return error_message
    all_dfs = []
    errors = []
    _log_debug(f"--- [外汇历史] 开始获取 {symbols} 从 {start_date} 到 {end_date} 的数据...")
    for symbol in symbols:
        df_or_error = _get_and_clean_forex_data(symbol)
        if isinstance(df_or_error, pd.DataFrame):
            all_dfs.append(df_or_error)
        else:
            errors.append(f"'{symbol}': 获取失败，错误: {df_or_error}")
    if not all_dfs:
        error_message = f"错误：未能成功获取任何一个品种的数据。详情: {'; '.join(errors)}"
        _log_debug(f"--- [外汇历史] {error_message} ---")
        return error_message
    if errors:
        _log_debug(f"--- [外汇历史] 警告：部分品种获取失败: {'; '.join(errors)} ---")
    try:
        combined_df = pd.concat(all_dfs, ignore_index=False) 
        mask = (combined_df.index >= start_date) & (combined_df.index <= end_date)
        filtered_df = combined_df.loc[mask].copy()
        if filtered_df.empty:
            error_message = f"错误：在指定日期范围 {start_date} 到 {end_date} 内没有找到任何数据。"
            _log_debug(f"--- [外汇历史] {error_message} ---")
            return error_message
        missing_cols = [col for col in columns_to_include if col not in filtered_df.columns]
        if '代码' not in filtered_df.columns:
            missing_cols.append('代码')
        if missing_cols:
            error_message = f"错误：API返回的数据中缺少必要的列: {missing_cols}。"
            _log_debug(f"--- [外汇历史] {error_message} ---")
            return error_message
        pivot_df = filtered_df.pivot_table(
            index=filtered_df.index,
            columns='代码',
            values=columns_to_include
        )
        return pivot_df
    except Exception as e:
        error_message = f"错误：在处理和重塑数据时发生错误: {e}"
        _log_debug(f"--- [外汇历史] {error_message} ---")
        return error_message


@lru_cache(maxsize=1)
def _load_index_data() -> Union[pd.DataFrame, str]:
    global _INDEX_DATA_CACHE
    if _INDEX_DATA_CACHE is not None:
        if isinstance(_INDEX_DATA_CACHE, pd.DataFrame):
            return _INDEX_DATA_CACHE
        _log_debug("--- [缓存警告] 缓存中为错误信息, 尝试重新加载... ---")
    _log_debug(f"--- [数据加载] 正在从 Pickle 文件 '{LOCAL_PICKLE_FILE}' 加载 '{PICKLE_INDEX_KEY}'... ---")
    if not os.path.exists(LOCAL_PICKLE_FILE):
        error_message = f"错误: Pickle 文件未找到! 路径: {LOCAL_PICKLE_FILE}"
        _log_debug(f"--- [数据加载] {error_message} ---")
        _INDEX_DATA_CACHE = error_message
        return error_message 
    try:
        with open(LOCAL_PICKLE_FILE, 'rb') as f:
            data_archive = pickle.load(f)
        if PICKLE_INDEX_KEY not in data_archive:
            error_message = f"错误: Pickle 归档中缺少键名 '{PICKLE_INDEX_KEY}' 的数据集。"
            _log_debug(f"--- [数据加载] {error_message} ---")
            _INDEX_DATA_CACHE = error_message
            return error_message
        df = data_archive[PICKLE_INDEX_KEY]
        if df.empty:
            error_message = f"错误：数据集 '{PICKLE_INDEX_KEY}' 加载成功，但 DataFrame 为空。"
            _log_debug(f"--- [数据加载] {error_message} ---")
            _INDEX_DATA_CACHE = error_message
            return error_message
        if 'index_code' in df.columns:
            df['index_code'] = df['index_code'].astype(str)
        df = df.set_index('display_name')
        _INDEX_DATA_CACHE = df
        _log_debug(f"成功加载并缓存索引数据: {PICKLE_INDEX_KEY}")
        return _INDEX_DATA_CACHE
    except KeyError as ke:
        error_message = f"错误: 文件中缺少必需的列: {ke}。"
        _log_debug(f"--- [数据加载] {error_message} ---")
        _INDEX_DATA_CACHE = error_message 
        return error_message
    except Exception as e:
        error_message = f"加载索引数据时发生未知错误: {e}"
        _log_debug(f"--- [数据加载] {error_message} ---")
        _INDEX_DATA_CACHE = error_message 
        return error_message


@lru_cache(maxsize=1)
def _load_pickle_archive() -> Union[Dict[str, pd.DataFrame], str]:
    if not os.path.exists(LOCAL_PICKLE_FILE):
        return f"错误: Pickle 文件未找到! 路径: {LOCAL_PICKLE_FILE}"
    try:
        with open(LOCAL_PICKLE_FILE, 'rb') as f:
            data_archive = pickle.load(f)
        if not isinstance(data_archive, dict):
            return "错误: Pickle 文件加载成功，但内容不是预期的字典类型。"
        _log_debug(f"--- [Cache] 成功加载并缓存 Pickle 归档 ({len(data_archive)} 个数据集)。 ---")
        return data_archive
    except Exception as e:
        return f"错误: 加载 Pickle 文件时出错: {e}"


@lru_cache(maxsize=1)
def _load_a_stock_data() -> Union[pd.DataFrame, str]:
    archive = _load_pickle_archive()
    if isinstance(archive, str): return archive
    if PICKLE_KEY_A not in archive:
        return f"错误: Pickle 归档中缺少键名 '{PICKLE_KEY_A}' 的数据集。"
    df = archive[PICKLE_KEY_A]
    if not isinstance(df, pd.DataFrame) or df.empty:
        return f"错误: Pickle 归档中 '{PICKLE_KEY_A}' 数据集为空或类型错误。"
    if not {'代码', '名称'}.issubset(df.columns):
        return f"错误: A股数据集 ('{PICKLE_KEY_A}') 缺少 '代码' 或 '名称' 列。"
    _log_debug(f"--- [Cache] A股数据加载成功。")
    return df


@lru_cache(maxsize=1)
def _load_hk_stock_data() -> Union[pd.DataFrame, str]:
    archive = _load_pickle_archive()
    if isinstance(archive, str): return archive 
    if PICKLE_KEY_HK not in archive:
        return f"错误: Pickle 归档中缺少键名 '{PICKLE_KEY_HK}' 的数据集。"
    df = archive[PICKLE_KEY_HK]
    if not isinstance(df, pd.DataFrame) or df.empty:
        return f"错误: Pickle 归档中 '{PICKLE_KEY_HK}' 数据集为空或类型错误。"
    if not {'代码', '中文名称'}.issubset(df.columns):
        return f"错误: 港股数据集 ('{PICKLE_KEY_HK}') 缺少 '代码' 或 '中文名称' 列。"
    _log_debug(f"--- [Cache] 港股数据加载成功。")
    return df


@lru_cache(maxsize=1)
def _load_us_stock_data() -> Union[pd.DataFrame, str]:
    archive = _load_pickle_archive()
    if isinstance(archive, str): return archive 
    if PICKLE_KEY_US not in archive:
        return f"错误: Pickle 归档中缺少键名 '{PICKLE_KEY_US}' 的数据集。"
    df = archive[PICKLE_KEY_US]
    if not isinstance(df, pd.DataFrame) or df.empty:
        return f"错误: Pickle 归档中 '{PICKLE_KEY_US}' 数据集为空或类型错误。"
    if not {'name', 'symbol', 'market'}.issubset(df.columns):
        return f"错误: 美股数据集 ('{PICKLE_KEY_US}') 缺少 'name', 'symbol', 或 'market' 列。"
    _log_debug(f"--- [Cache] 美股数据加载成功。")
    return df


def _create_map_from_df(df: pd.DataFrame, name_col: str, code_col: str) -> Dict[str, str]:
    """[辅助函数] 从DataFrame创建 {name: code} 字典的辅助函数"""
    df_unique = df.drop_duplicates(subset=[name_col])
    stock_map = pd.Series(
        df_unique[code_col].values, 
        index=df_unique[name_col]
    ).to_dict()
    return stock_map


def _estimate_tokens(text: str) -> int:
    """估算文本的 token 数量。使用简单的估算方法：每 4 个字符约等于 1 个 token。"""
    return len(text) // 4 + 1


def _truncate_json_content(content: Any, max_tokens: int) -> Tuple[Any, int]:
    """确定性地截断 JSON 内容以符合 max_tokens 限制。返回截断后的内容和实际使用的 token 数。"""
    content_str = json.dumps(content, ensure_ascii=False, indent=2)
    estimated_tokens = _estimate_tokens(content_str)
    
    if estimated_tokens <= max_tokens:
        return content, estimated_tokens
    
    # 如果内容超过限制，需要截断
    # 使用简单的策略：将 JSON 字符串截断到合适的长度
    max_chars = max_tokens * 4
    truncated_str = content_str[:max_chars]
    
    # 尝试解析截断后的字符串，如果失败则进一步截断
    try:
        truncated_content = json.loads(truncated_str)
        actual_tokens = _estimate_tokens(truncated_str)
        return truncated_content, actual_tokens
    except json.JSONDecodeError:
        # 如果截断导致 JSON 无效，尝试找到最后一个完整的 JSON 对象
        # 简单策略：截断到最后一个完整的键值对
        last_brace = truncated_str.rfind('}')
        if last_brace > 0:
            truncated_str = truncated_str[:last_brace + 1]
            try:
                truncated_content = json.loads(truncated_str)
                actual_tokens = _estimate_tokens(truncated_str)
                return truncated_content, actual_tokens
            except json.JSONDecodeError:
                pass
        
        # 如果仍然失败，返回一个简单的错误消息
        error_content = {"error": "Content truncated due to token limit"}
        error_str = json.dumps(error_content, ensure_ascii=False)
        return error_content, _estimate_tokens(error_str)

