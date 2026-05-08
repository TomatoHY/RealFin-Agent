import akshare as ak
import pandas as pd

from typing import Optional, Union, List

from ..utils import _get_futures_symbol_map, _log_debug


def get_futures_history(
    identifier: str,
    start_date: str,
    end_date: str,
    columns_to_include: Optional[List[str]] = None
) -> Union[pd.DataFrame, str]:
    """
    获取【单个期货主力连续合约】在【指定时间段内】的日度历史行情数据。
    用户可以指定需要返回的数据列。
    
    :param identifier: 期货品种的代码或中文名称。例如 "IF0" 或 "沪深300指数期货"。
    :param start_date: 开始日期, 格式 'YYYY-MM-DD'.
    :param end_date: 结束日期, 格式 'YYYY-MM-DD'.
    :param columns_to_include: (可选) 一个包含所需数据列名的列表。
                            有效值: ['开盘价', '最高价', '最低价', '收盘价', '成交量', '持仓量', '动态结算价']。
                            默认为返回所有列。
    :return: 一个包含指定期货历史数据的 pandas.DataFrame 对象, 或一个错误信息字符串。
    """
    _log_debug(f"--- [期货查询] Manging '{identifier}' 从 {start_date} 到 {end_date} 的历史数据... ---")
    symbol_map_or_error = _get_futures_symbol_map()
    if isinstance(symbol_map_or_error, str):
        _log_debug(f"--- [期货查询] 内部函数返回错误: {symbol_map_or_error} ---")
        return symbol_map_or_error  
    symbol_map = symbol_map_or_error
    if not symbol_map: 
        error_message = "错误：无法获取期货品种列表（内部函数返回为空），无法继续查询。"
        _log_debug(f"--- [期货查询] {error_message} ---")
        return error_message
    normalized_identifier = identifier.lower().replace('连续', '')
    symbol = symbol_map.get(normalized_identifier)
    if not symbol:
        for name, sym in symbol_map.items():
            if isinstance(name, str) and normalized_identifier in name.lower():
                symbol = sym
                _log_debug(f"--- [期货查询] 模糊匹配到 '{name}' -> 代码 '{symbol}' ---")
                break
    if not symbol:
        error_message = f"错误: 未能识别期货品种 '{identifier}'。请检查代码或名称是否正确。有效选项（部分）: {list(symbol_map.keys())[:10]}..."
        _log_debug(f"--- [期货查询] {error_message} ---")
        return error_message
    DEFAULT_COLUMNS = ['开盘价', '最高价', '最低价', '收盘价', '成交量', '持仓量', '动态结算价']
    final_columns = DEFAULT_COLUMNS
    if columns_to_include:
        invalid_columns = [col for col in columns_to_include if col not in DEFAULT_COLUMNS]
        if invalid_columns:
            error_message = f"错误: 请求了无效的列名 {invalid_columns}。有效选项: {DEFAULT_COLUMNS}"
            _log_debug(f"--- [期货查询] {error_message} ---")
            return error_message
        final_columns = columns_to_include
    try:
        start_date_fmt = start_date.replace('-', '')
        end_date_fmt = end_date.replace('-', '')
        df = ak.futures_main_sina(symbol=symbol, start_date=start_date_fmt, end_date=end_date_fmt)
        if df.empty:
            error_message = f"信息: 在时间范围 {start_date} 到 {end_date} 内没有找到 '{identifier}' (代码: {symbol}) 的任何数据。"
            _log_debug(f"--- [期货查询] {error_message} ---")
            return error_message 
        missing_cols = ['日期'] + [col for col in final_columns if col not in df.columns]
        if len(missing_cols) > 1 or '日期' not in missing_cols:
            error_message = f"错误：API返回的数据中缺少请求的列: {missing_cols}。"
            _log_debug(f"--- [期货查询] {error_message} ---")
            return error_message
        return df[['日期'] + final_columns]
    except Exception as e:
        error_message = f"错误：在为 '{identifier}' (代码: {symbol}) 查询API时发生错误: {e}"
        _log_debug(f"--- [期货查询] {error_message} ---")
        return error_message
