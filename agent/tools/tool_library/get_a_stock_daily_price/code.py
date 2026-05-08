import pandas as pd

from datetime import datetime, timedelta
from typing import Optional, Any, Dict

from ..get_code_from_name.code import get_code_from_name
from ..utils import LATEST_KEYWORDS, _fetch_a_history_hybrid, _fetch_a_realtime_hybrid, _log_debug


def get_a_stock_daily_price(
column_label: str,
    adjust: str,
    query_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    name: Optional[str] = None,
    code: Optional[str] = None,
    original_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取A股实时或历史行情数据。
    """
    COLUMN_MAPPING = {
        'open': '开盘', 'high': '最高', 'low': '最低', 'close': '收盘',
        'volume': '成交量', 'amount': '成交额',
        '开盘': '开盘', '最高': '最高', '最低': '最低',
        '收盘': '收盘', '最新价': '收盘', 
        '成交量': '成交量', '成交额': '成交额',
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
    resolved_symbol = None  
    resolved_ts_code = None 
    resolved_ak_code = None 
    try:
        if code:
            resolved_symbol = str(code)
        elif name:
            _log_debug(f"--- [A股] 'code' 未提供, 正在使用 'name' ({name}) 从 [本地缓存] 查找代码... ---")
            found_code = get_code_from_name(name=name, market='a') 
            if not found_code or "--- [LocalSearch] 查找" in str(found_code):
                return _fail(f"错误: 无法通过名称 '{name}' 从 [本地缓存] 找到对应的股票代码。{found_code}")
            resolved_symbol = str(found_code)
        if not resolved_symbol:
            return _fail(f"错误: 无法解析 '{identifier}' 为有效的股票代码。")
        if resolved_symbol.startswith('sh'):
            resolved_ak_code = resolved_symbol[2:]
            resolved_ts_code = resolved_ak_code + ".SH"
        elif resolved_symbol.startswith('sz'):
            resolved_ak_code = resolved_symbol[2:]
            resolved_ts_code = resolved_ak_code + ".SZ"
        elif resolved_symbol.startswith('bj'):
            resolved_ak_code = resolved_symbol[2:]
            resolved_ts_code = resolved_ak_code + ".BJ"
        else:
            return _fail(f"错误: 解析的代码 '{resolved_symbol}' 缺少 'sh', 'sz' 或 'bj' 前缀。")
    except Exception as e:
        return _fail(f"在为 '{identifier}' 解析代码时失败: {e}")
    is_latest_query = (query_date and query_date.lower().strip() in LATEST_KEYWORDS) or \
                    (original_query and any(k in original_query.lower() for k in LATEST_KEYWORDS))
    if is_latest_query:
        _log_debug(f"--- [A股实时] 执行 [{identifier}] 的实时数据查询 (Ashare > Akshare) ---")
        clean_column_label = column_label.lower().strip()
        hist_col = COLUMN_MAPPING.get(clean_column_label) # [新] 简化的映射
        if not hist_col:
            return _fail(f"错误: 列名 '{clean_column_label}' 在 COLUMN_MAPPING 中未定义。")
        realtime_row, source = _fetch_a_realtime_hybrid(
            resolved_symbol=resolved_symbol,
            resolved_ts_code=resolved_ts_code,
            target_col=hist_col 
        )
        if realtime_row is None:
            return _fail(f"错误: 所有实时源 (Ashare, Akshare) 均未能获取 '{identifier}' 的数据。")
        try:
            clean_column_label = column_label.lower().strip()
            hist_col = COLUMN_MAPPING.get(clean_column_label) # [新] 简化的映射
            if not hist_col:
                return _fail(f"错误: 列名 '{clean_column_label}' 在 COLUMN_MAPPING 中未定义。")
            if hist_col not in realtime_row:
                return _fail(f"错误: 实时数据 (源: {source}) 中缺少必需列 '{hist_col}' (映射自 '{clean_column_label}')。")
            value = realtime_row[hist_col]
            query_date_str = realtime_row['日期']
            return { "result": float(value), "stock_identifier": resolved_symbol, "market": "A-Share",
                    "date": query_date_str, "requested_item": {"name": clean_column_label, "value": float(value)} }
        except Exception as e:
            return _fail(f"处理 '{identifier}' (源: {source}) 的实时数据时发生未知错误: {e}")
    _log_debug(f"--- [A股历史] 执行 [{identifier}] 的历史数据查询 (Akshare/Ashare) ---")
    df_hist, source = _fetch_a_history_hybrid(
        resolved_symbol=resolved_symbol,
        resolved_ts_code=resolved_ts_code,
        resolved_ak_code=resolved_ak_code,
        adjust=adjust,
        start_date=start_date if start_date else "19700101",
        end_date=end_date or query_date or datetime.now().strftime('%Y-%m-%d')
    )
    if df_hist is None: 
        return _fail(f"错误: 历史源 (Akshare/Ashare) 无法获取 '{identifier}' 的历史数据。")
    try:
        clean_column_label = column_label.lower().strip()
        hist_col = COLUMN_MAPPING.get(clean_column_label)
        if not hist_col or hist_col not in df_hist.columns:
            valid_cols = [col for col in ['开盘','收盘','最高','最低','成交量','成交额'] if col in df_hist.columns]
            return _fail(f"错误: A股历史数据(源: {source})中列名 '{clean_column_label}' (映射: {hist_col}) 无效。可用列: {valid_cols}")
        if start_date: # 范围查询
            effective_end_date = end_date or query_date 
            if effective_end_date is None:
                effective_end_date = datetime.now().strftime('%Y-%m-%d')
            df_hist['日期'] = pd.to_datetime(df_hist['日期'])
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(effective_end_date)
            range_df = df_hist[(df_hist['日期'] >= start_dt) & (df_hist['日期'] <= end_dt)].copy()
            if range_df.empty: 
                return _fail(f"错误: 在指定日期范围 {start_date} 到 {effective_end_date} 内未找到任何数据。")
            range_df[hist_col] = pd.to_numeric(range_df[hist_col], errors='coerce')
            min_row = range_df.loc[range_df[hist_col].idxmin()]
            min_val = float(min_row[hist_col])
            return {
                "result": min_val, "query_type": "range_minimum", "stock_identifier": resolved_symbol, 
                "min_value": min_val, "date_of_min_value": min_row['日期'].strftime('%Y-%m-%d'),
                "requested_item": {"name": clean_column_label, "value": min_val}
            }
        else: # 单点查询
            df_hist['日期'] = pd.to_datetime(df_hist['日期'])
            target_dt = pd.to_datetime(query_date)
            row_found = pd.DataFrame()
            _log_debug(f"--- 未找到精确日期 '{query_date}'，正在回退查找最近的有效交易日... ---")
            for i in range(7): # 7 天回溯
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
                "result": value, "query_type": "single_date", "stock_identifier": resolved_symbol,
                "date": actual_date, "requested_item": {"name": clean_column_label, "value": value}
            }
    except Exception as e:
        return _fail(f"处理 '{identifier}' (源: {source}) 的历史数据时发生未知错误: {e}")
