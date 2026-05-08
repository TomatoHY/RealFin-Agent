import time

import akshare as ak
import pandas as pd

from datetime import datetime
from typing import Optional, Any, Dict

from ..utils import LATEST_KEYWORDS, _fetch_us_spot_data, _log_debug, _normalize_stock_name


def get_us_stock_daily_price(
column_label: str,
    adjust: str,
    query_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    name: Optional[str] = None,
    code: Optional[str] = None,
    original_query: Optional[str] = None
) -> Dict[str, Any]:
    COLUMN_MAPPING = {
        'open':           {'spot_us': 'open', 'hist': '开盘'},
        'high':           {'spot_us': 'high', 'hist': '最高'},
        'low':            {'spot_us': 'low', 'hist': '最低'},
        'close':          {'spot_us': 'price', 'hist': '收盘'},
        'latest_price':   {'spot_us': 'price', 'hist': '收盘'},
        'volume':         {'spot_us': 'volume', 'hist': '成交量'},
        'amount':         {'spot_us': 'mktcap', 'hist': '成交额'}, 
        'market_cap':     {'spot_us': 'mktcap', 'hist': '成交额'}, 
        'change_percent': {'spot_us': 'chg_percent', 'hist': '涨跌幅'},
        'pe_ratio':       {'spot_us': 'pe', 'hist': '市盈率(TTM)'},
    }
    def _fail(error_msg: str) -> Dict[str, Any]:
        return {
            "result": error_msg,
            "min_value": None,
            "requested_item": {"value": None, "error": error_msg}
        }
    if adjust not in ['', 'qfq', 'hfq']: return _fail(f"错误: 'adjust' 参数 '{adjust}' 无效。")
    if not code and not name: return _fail("错误: 必须提供股票代码 (code) 或股票名称 (name)。")
    if not query_date and not start_date: return _fail("错误: 必须提供 `query_date` 或 `start_date`。")
    identifier = name if name else code 
    is_latest_query = (query_date and query_date.lower().strip() in LATEST_KEYWORDS) or \
                    (original_query and any(k in original_query.lower() for k in LATEST_KEYWORDS))
    if is_latest_query:
        _log_debug(f"--- [美股实时] 执行 [{identifier}] 的实时数据查询 (来源: API + Cache) ---")
        df_realtime = _fetch_us_spot_data()
        if df_realtime is None:
            return _fail(f"错误: 无法从 API 获取实时数据快照 (ak.stock_us_spot)。")
        realtime_row_match = pd.DataFrame() 
        search_ticker = ""
        if code:
            search_ticker = code.upper()
            realtime_row_match = df_realtime[df_realtime['symbol'] == search_ticker]
        elif name:
            normalized_input = _normalize_stock_name(name)
            realtime_row_match = df_realtime[df_realtime['normalized_name'].str.contains(normalized_input, na=False)]
            if not realtime_row_match.empty: 
                search_ticker = realtime_row_match.iloc[0]['symbol']
        if realtime_row_match.empty:
            return _fail(f"错误: 在实时 API 数据中未找到 '{identifier}'。")
        realtime_row = realtime_row_match.iloc[0]
        clean_column_label = column_label.lower().strip()
        spot_col_name = COLUMN_MAPPING.get(clean_column_label, {}).get('spot_us')
        if not spot_col_name:
            return _fail(f"错误: 列名 '{clean_column_label}' 在美股 COLUMN_MAPPING 中没有定义 'spot_us' 键。")
        if spot_col_name not in realtime_row:
            return _fail(f"错误: 实时数据中缺少必需列 '{spot_col_name}' (映射自 '{clean_column_label}')。")
        value = realtime_row[spot_col_name]
        if pd.isna(value): 
            return _fail(f"错误: 实时数据中 '{clean_column_label}' 的值不可用。")
        query_date_str = datetime.now().strftime('%Y-%m-%d')
        return {
            "result": float(value),
            "requested_item": {"name": clean_column_label, "value": float(value)},
            "min_value": float(value), 
            "query_type": "single_date", "stock_identifier": search_ticker,
            "date": query_date_str,
        }
    _log_debug(f"--- [美股历史] 执行 [{identifier}] 的历史数据查询 (来源: API接口) ---")
    if not code:
        return _fail(f"错误: 历史查询必须提供 'code' (股票代码, e.g., 'MSFT')。")
    search_ticker = code.upper()
    possible_symbols = [
        f"105.{search_ticker}", # 纳斯达克 (e.g., MSFT, AAPL, NVDA)
        f"106.{search_ticker}", # 纽约 (e.g., TTE, JPM)
        f"107.{search_ticker}"  # 美交所
    ]
    df_hist = None
    symbol_for_hist = ""
    for symbol in possible_symbols:
        try:
            _log_debug(f"--- [美股历史] 正在尝试使用 Symbol '{symbol}' 调用 ak.stock_us_hist()... ---")
            df_hist_attempt = ak.stock_us_hist(symbol=symbol, adjust=adjust, start_date="19700101", end_date="20991231") 
            if df_hist_attempt is not None and not df_hist_attempt.empty:
                df_hist = df_hist_attempt
                symbol_for_hist = symbol
                _log_debug(f"--- [美股历史] 成功: Symbol '{symbol}' 返回了数据。")
                break 
            else:
                _log_debug(f"--- [美股历史] 失败: Symbol '{symbol}' 未返回数据。")
        except Exception as e:
            _log_debug(f"--- [美股历史] 失败: Symbol '{symbol}' 调用失败: {e}")
        _log_debug("   -> (暂停 2 秒...)")
        time.sleep(30) 
    if df_hist is None:
        return _fail(f"错误: 无法使用任何猜测的 symbol (e.g., 105.{search_ticker}, 106.{search_ticker}) 获取 '{search_ticker}' 的历史数据。")
    try:
        if '日期' not in df_hist.columns:
            return _fail(f"错误: 获取到的历史数据缺少 '日期' 列。")
        df_hist['日期'] = pd.to_datetime(df_hist['日期']).dt.strftime('%Y-%m-%d')
        df_hist.sort_values(by='日期', ascending=False, inplace=True)
        df_hist.reset_index(drop=True, inplace=True)
        clean_column_label = column_label.lower().strip()
        hist_col = COLUMN_MAPPING.get(clean_column_label, {}).get('hist')
        if not hist_col or hist_col not in df_hist.columns:
            valid_cols = [k for k, v in COLUMN_MAPPING.items() if v.get('hist') in df_hist.columns]
            return _fail(f"错误: 美股历史数据中列名 '{clean_column_label}' 无效。可用列: {valid_cols}")
        if start_date: # 范围查询
            effective_end_date = end_date or query_date 
            if effective_end_date is None:
                effective_end_date = datetime.now().strftime('%Y-%m-%d')
            range_df = df_hist[(df_hist['日期'] >= start_date) & (df_hist['日期'] <= effective_end_date)].copy()
            if range_df.empty:
                return _fail(f"错误: 在美股 {start_date} 到 {effective_end_date} 内未找到任何数据。")
            min_value_row = range_df.loc[range_df[hist_col].idxmin()]
            min_val = float(min_value_row[hist_col])
            return {
                "result": min_val, 
                "requested_item": {"name": clean_column_label, "value": min_val},
                "query_type": "range_minimum", 
                "stock_identifier": search_ticker,
                "min_value": min_val, 
                "date_of_min_value": min_value_row['日期']
            }
        else: # 单点查询
            row_found = df_hist[df_hist['日期'] == query_date]
            if row_found.empty:
                _log_debug(f"--- [美股历史] 未找到精确日期 '{query_date}'，正在回退... ---")
                row_found = df_hist[df_hist['日期'] <= query_date].head(1)
            if row_found.empty:
                return _fail(f"错误: 未找到美股日期 '{query_date}' 或更早的数据。")
            value = float(row_found.iloc[0][hist_col])
            return {
                "result": value, 
                "requested_item": {"name": clean_column_label, "value": value},
                "min_value": value, 
                "query_type": "single_date", "stock_identifier": search_ticker,
                "date": row_found.iloc[0]['日期'],
            }
    except Exception as e:
        return _fail(f"处理 '{search_ticker}' 的美股历史数据时发生未知错误: {e}")
