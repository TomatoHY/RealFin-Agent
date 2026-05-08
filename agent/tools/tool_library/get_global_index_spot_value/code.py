import time

import akshare as ak
import pandas as pd

from ..utils import CACHE_TTL_SECONDS, INDEX_ALIAS_MAP, _log_debug, _normalize_name, _global_spot_cache, _cache_timestamp


def get_global_index_spot_value(
name_or_code: str,
    column_label: str,
    force_refresh: bool = False,
    **kwargs
) -> str:
    """
    通过名称、代码或别名，获取全球主要指数的【最新实时行情数据】。
    """
    if 'date' in kwargs or 'query_date' in kwargs:
        return (
            "错误：参数使用错误。此工具是【实时数据专用工具】，"
            "不接受 'date' 或 'query_date' 等任何日期参数。"
            "如需查询历史数据，请使用其他工具。"
        )
    global _global_spot_cache, _cache_timestamp
    is_cache_stale = (time.time() - _cache_timestamp) > CACHE_TTL_SECONDS
    if force_refresh or _global_spot_cache is None or is_cache_stale:
        if force_refresh: _log_debug(f"--- [实时指数] 已触发缓存强制刷新 (latest/最新)。---")
        if is_cache_stale: _log_debug(f"--- [实时指数] 缓存已超过{CACHE_TTL_SECONDS}秒，自动刷新。---")
        _log_debug("--- [实时指数] 正在从 akshare 下载全球指数实时快照...")
        try:
            spot_df = ak.index_global_spot_em()
            if spot_df.empty:
                _global_spot_cache, _cache_timestamp = pd.DataFrame(), 0
            else:
                _global_spot_cache, _cache_timestamp = spot_df, time.time()
                _log_debug(f"--- [实时指数] 成功缓存 {len(_global_spot_cache)} 条全球指数快照。---")
        except Exception as e:
            _global_spot_cache, _cache_timestamp = pd.DataFrame(), 0
            return f"错误: 调用 ak.index_global_spot_em 接口失败: {e}"
    if _global_spot_cache.empty:
        return "错误: 全球指数实时快照数据当前不可用。"
    df = _global_spot_cache
    normalized_input = _normalize_name(name_or_code)
    target_identifier = INDEX_ALIAS_MAP.get(normalized_input, name_or_code)
    df['代码'] = df['代码'].astype(str)
    match = df[df['代码'].str.lower() == target_identifier.lower()]
    if match.empty:
        normalized_df_names = df['名称'].astype(str).apply(normalize_name)
        match = df[normalized_df_names == _normalize_name(target_identifier)]
    if match.empty:
        return f"错误: 未能找到名为 '{name_or_code}' 的指数。"
    column_map = {
        'code': '代码', 'name': '名称', 'close': '最新价', 'change': '涨跌额',
        'change_percent': '涨跌幅', 'previous_close': '昨收价', 'amplitude': '振幅',
        'last_update_time': '最新行情时间', 'high': '最高价', 'low': '最低价'
    }
    if column_label not in column_map:
        return f"错误: 列 '{column_label}' 无效。有效列为: {list(column_map.keys())}"
    actual_column = column_map[column_label]
    if actual_column not in df.columns:
        return f"错误: 数据源中不存在名为 '{actual_column}' 的列。"
    row_data = match.iloc[0]
    requested_value = row_data[actual_column]
    result_json = {
        "index_name": row_data.get('名称'),
        "index_code": row_data.get('代码'),
        "data_type": "latest_realtime_spot",
        "requested_item": {
            "label": column_label,
            "value": requested_value
        },
        "full_quote": {
            "latest_price": row_data.get('最新价'),
            "change_value": row_data.get('涨跌额'),
            "change_percent": row_data.get('涨跌幅'),
            "open_price": row_data.get('今开'),
            "high_price": row_data.get('最高'),
            "low_price": row_data.get('最低'),
            "previous_close": row_data.get('昨收'),
            "amplitude": row_data.get('振幅'),
            "quote_time": row_data.get('数据时间')
        }
    }
    return result_json
