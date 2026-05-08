from typing import Optional

from ..utils import _load_all_stock_data, _log_debug, _normalize_stock_name, _stock_data_cache, STOCK_DATA_KEYS


def get_code_from_name(
name: str, market: str = 'all'
):
    """
    从股票名称查找股票代码。

    Returns:
        str: 股票代码（成功时）
        dict: 错误信息字典（失败时），包含 error, error_type, tool_name 等字段
    """
    global _stock_data_cache, STOCK_DATA_KEYS
    _log_debug(f"--- [LocalSearch] 开始为 '{name}' 在市场 '{market}' 中查找股票代码 ---")
    if not _load_all_stock_data():
        return {
            "error": f"查找失败。无法加载本地数据归档。",
            "error_type": "DATA_LOAD_ERROR",
            "tool_name": "get_code_from_name",
            "input_name": name,
            "market": market
        }
    market_map = { 'a': 'a_shares', 'hk': 'hk_shares', 'us': 'us_shares' }
    sources_to_search = []
    if market in market_map:
        key = market_map[market]
        if key in STOCK_DATA_KEYS:
            sources_to_search.append(key)
    else:
        sources_to_search = list(STOCK_DATA_KEYS.keys())
    normalized_input = _normalize_stock_name(name)
    for cache_key in sources_to_search:
        df = _stock_data_cache.get(cache_key)
        if df is None or df.empty:
            continue
        _, name_col, code_col = STOCK_DATA_KEYS[cache_key]
        normalized_df_names = df['normalized_name']
        exact_match_rows = df[normalized_df_names == normalized_input]
        if not exact_match_rows.empty:
            stock_row = exact_match_rows.iloc[0]
            raw_code = stock_row[code_col]
            stock_code = str(raw_code).split('.')[0]
            _log_debug(f"*** [LocalSearch] 成功! 在 {cache_key} 中【精确匹配】到 '{stock_row[name_col]}' 的代码是: {stock_code} (原始值: {raw_code}) ***")
            return stock_code
        if len(normalized_input) > 1:
            contain_match_rows = df[normalized_df_names.str.contains(normalized_input, na=False)]
            if not contain_match_rows.empty:
                stock_row = contain_match_rows.iloc[0]
                raw_code = stock_row[code_col]
                stock_code = str(raw_code).split('.')[0]
                _log_debug(f"*** [LocalSearch] 成功! 在 {cache_key} 中【模糊匹配】到 '{stock_row[name_col]}' 的代码是: {stock_code} (原始值: {raw_code}) ***")
                return stock_code

    # 返回标准错误格式而不是字符串
    return {
        "error": f"在指定范围未能找到与 '{name}' 相关的股票代码。",
        "error_type": "NOT_FOUND",
        "tool_name": "get_code_from_name",
        "input_name": name,
        "market": market,
        "searched_markets": sources_to_search,
        "suggestion": "请检查股票名称是否正确，或尝试使用其他市场参数（'a' for A股, 'hk' for 港股, 'us' for 美股）"
    }
