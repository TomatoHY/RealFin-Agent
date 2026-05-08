import pandas as pd

from datetime import datetime, timedelta
from typing import Optional, Any, Dict

from ..utils import LATEST_KEYWORDS, _fetch_hk_history, _fetch_hk_spot_data, _log_debug, _normalize_stock_name, _hk_history_cache_akshare


def get_hk_stock_daily_price(
column_label: str,
    adjust: str = '',
    query_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    name: Optional[str] = None,
    code: Optional[str] = None,
    original_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取港股实时或历史行情数据。
    """
    COLUMN_MAPPING = {
        'open': {'spot_hk': '今开', 'hist': '开盘'},
        'high': {'spot_hk': '最高', 'hist': '最高'},
        'low': {'spot_hk': '最低', 'hist': '最低'},
        'close': {'spot_hk': '最新价', 'hist': '收盘'},
        'latest_price': {'spot_hk': '最新价', 'hist': '收盘'},
        'volume': {'spot_hk': '成交量', 'hist': '成交量'},
        'amount': {'spot_hk': '成交额', 'hist': '成交额'},
        'change_percent': {'spot_hk': '涨跌幅', 'hist': '涨跌幅'}, 
        'pct_change': {'spot_hk': '涨跌幅', 'hist': '涨跌幅'},
        '开盘':   {'spot_hk': '今开', 'hist': '开盘'},
        '最高':   {'spot_hk': '最高', 'hist': '最高'},
        '最低':   {'spot_hk': '最低', 'hist': '最低'},
        '收盘':   {'spot_hk': '最新价', 'hist': '收盘'},
        '最新价': {'spot_hk': '最新价', 'hist': '收盘'},
        '成交量': {'spot_hk': '成交量', 'hist': '成交量'},
        '成交额': {'spot_hk': '成交额', 'hist': '成交额'},
        '涨跌幅': {'spot_hk': '涨跌幅', 'hist': '涨跌幅'},
    }
    
    def _fail(error_msg: str) -> Dict[str, Any]:
        return {
            "result": error_msg,
            "min_value": None, 
            "requested_item": {"value": None, "error": error_msg}, 
            "date": datetime.now().strftime('%Y-%m-%d') 
        }
    
    if adjust not in ['', 'qfq', 'hfq']: 
        return _fail(f"错误: 'adjust' 参数 '{adjust}' 无效。")
    if not code and not name: return _fail("错误: 必须提供股票代码 (code) 或股票名称 (name)。")
    if not query_date and not start_date: return _fail("错误: 必须提供 `query_date` 或 `start_date`。")
    identifier = name if name else code 
    is_latest_query = (query_date and query_date.lower().strip() in LATEST_KEYWORDS) or \
                    (original_query and any(k in original_query.lower() for k in LATEST_KEYWORDS))
    if is_latest_query:
        _log_debug(f"--- [港股实时] 执行 [{identifier}] 的实时数据查询 (来源: Akshare) ---")
        df_realtime = _fetch_hk_spot_data()
        if df_realtime is None:
            return _fail(f"错误: 无法从 API 获取实时数据快照 (ak.stock_hk_spot)。")
        realtime_row_match = pd.DataFrame()
        search_code = ""
        if code:
            search_code = str(code).zfill(5)
            realtime_row_match = df_realtime[df_realtime['代码'] == search_code]
        elif name: 
            normalized_input = _normalize_stock_name(name)
            exact_match = df_realtime[df_realtime['normalized_name'] == normalized_input]
            if not exact_match.empty:
                realtime_row_match = exact_match
                search_code = realtime_row_match.iloc[0]['代码']
            else:
                contain_match = df_realtime[df_realtime['normalized_name'].str.contains(normalized_input, na=False)]
                if not contain_match.empty:
                    realtime_row_match = contain_match.head(1)
                    search_code = realtime_row_match.iloc[0]['代码']
        if realtime_row_match.empty:
            return _fail(f"错误: 在实时 API 数据中未找到 '{identifier}'。")
        realtime_row = realtime_row_match.iloc[0]
        display_name = realtime_row['中文名称']
        clean_column_label = column_label.lower().strip()
        spot_col_name = COLUMN_MAPPING.get(clean_column_label, {}).get('spot_hk')
        if not spot_col_name:
            return _fail(f"错误: 列名 '{clean_column_label}' 在 COLUMN_MAPPING 中没有定义 'spot_hk' 键。")
        if spot_col_name not in realtime_row:
            fallback_col = '最新' if spot_col_name == '最新价' else None
            if fallback_col and fallback_col in realtime_row:
                spot_col_name = fallback_col
            else:
                return _fail(f"错误: 实时数据中缺少必需列 '{spot_col_name}' (映射自 '{clean_column_label}')。")
        value = realtime_row[spot_col_name]
        if pd.isna(value): 
            return _fail(f"错误: 实时数据中 '{clean_column_label}' (API列: {spot_col_name}) 的值不可用。")
        query_date_str = datetime.now().strftime('%Y-%m-%d')
        return {
            "result": float(value), 
            "query_type": "single_date", 
            "stock_identifier": search_code,
            "date": query_date_str,
            "requested_item": {"name": clean_column_label, "value": float(value)}
        }
    _log_debug(f"--- [港股历史] 执行 [{identifier}] 的历史数据查询 (Akshare) ---")
    symbol_akshare = None 
    display_name = identifier 
    if code:
        symbol_akshare = str(code).zfill(5)
        display_name = symbol_akshare
    elif name:
        _log_debug(f"--- [港股历史] 'name' ({name}) 已提供, 正在 [Akshare 实时缓存] 查找代码... ---")
        df_realtime_cache = _fetch_hk_spot_data()
        if df_realtime_cache is None:
            return _fail(f"错误: 无法获取实时数据快照，无法通过名称找到代码。")
        normalized_input = _normalize_stock_name(name)
        exact_match = df_realtime_cache[df_realtime_cache['normalized_name'] == normalized_input]
        stock_row = None
        if not exact_match.empty:
            stock_row = exact_match.iloc[0]
        else:
            contain_match = df_realtime_cache[df_realtime_cache['normalized_name'].str.contains(normalized_input, na=False)]
            stock_row = contain_match.head(1).iloc[0] if not contain_match.empty else None
        if stock_row is None:
            return _fail(f"错误: 无法在 API 实时数据中通过名称 '{name}' 找到代码。")
        symbol_akshare = str(stock_row['代码']).zfill(5)
        display_name = stock_row['中文名称']
        _log_debug(f"--- [港股历史] 成功在API缓存中找到代码: {symbol_akshare} ---")
    if not symbol_akshare:
        return _fail(f"错误: 历史查询未能确定股票代码。")
    df_hist = None
    source = "Unknown"
    _log_debug(f"--- [HK Akshare] 正在使用 Akshare 数据源... ---")
    global _hk_history_cache_akshare
    cache_key_akshare = (symbol_akshare, adjust)
    df_hist = _hk_history_cache_akshare.get(cache_key_akshare)
    if df_hist is None:
        df_hist = _fetch_hk_history(symbol=symbol_akshare, adjust=adjust)
        if df_hist is None: 
            return _fail(f"错误: Akshare 无法获取 '{display_name}' 的历史数据。")
        _hk_history_cache_akshare[cache_key_akshare] = df_hist
        _log_debug("--- [HK Akshare] 成功获取数据。")
    else:
        _log_debug("--- [HK Akshare] 缓存命中。")
    source = "Akshare"
    try:
        clean_column_label = column_label.lower().strip()
        hist_col = COLUMN_MAPPING.get(clean_column_label, {}).get('hist')
        if not hist_col or hist_col not in df_hist.columns:
            if not hist_col or hist_col not in df_hist.columns:
                valid_cols = [v.get('hist') for v in COLUMN_MAPPING.values() if v.get('hist') in df_hist.columns]
                return _fail(f"错误: 历史数据(源: {source})中列名 '{clean_column_label}' (映射: {hist_col}) 无效。可用列: {valid_cols}")
        if start_date: # 范围查询
            effective_end_date = end_date or query_date 
            if effective_end_date is None:
                effective_end_date = datetime.now().strftime('%Y-%m-%d')
            df_hist['日期'] = pd.to_datetime(df_hist['日期'])
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(effective_end_date)
            range_df = df_hist[(df_hist['日期'] >= start_dt) & (df_hist['日期'] <= end_dt)]
            if range_df.empty: 
                return _fail(f"错误: 在指定日期范围 {start_date} 到 {effective_end_date} 内未找到任何数据。")
            range_df[hist_col] = pd.to_numeric(range_df[hist_col], errors='coerce')
            min_row = range_df.loc[range_df[hist_col].idxmin()]
            min_val = float(min_row[hist_col])
            return {
                "result": min_val, 
                "query_type": "range_minimum", 
                "stock_identifier": symbol_akshare, 
                "min_value": min_val, 
                "date_of_min_value": min_row['日期'].strftime('%Y-%m-%d'),
                "requested_item": {"name": clean_column_label, "value": min_val}
            }
        else: # 单点查询
            df_hist['日期'] = pd.to_datetime(df_hist['日期'])
            target_dt = pd.to_datetime(query_date)
            row_found = pd.DataFrame()
            _log_debug(f"--- 正在查找精确日期 '{query_date}' (带7天回溯)... ---")
            for i in range(7):
                current_target_dt = target_dt - timedelta(days=i)
                row_found = df_hist[df_hist['日期'] == current_target_dt]
                if not row_found.empty:
                    break
            if row_found.empty:
                min_d, max_d = df_hist['日期'].min(), df_hist['日期'].max()
                return _fail(f"错误: 未找到日期 '{query_date}' 或任何更早的数据。可用数据范围: {min_d} 到 {max_d}。")
            value = float(row_found.iloc[0][hist_col])
            actual_date = row_found.iloc[0]['日期'].strftime('%Y-%m-%d')
            return {
                "result": value, 
                "query_type": "single_date", 
                "stock_identifier": symbol_akshare,
                "date": actual_date,
                "requested_item": {"name": clean_column_label, "value": value}
            }
    except Exception as e:
        return _fail(f"处理 '{display_name}' (源: {source}) 的历史数据时发生未知错误: {e}")
