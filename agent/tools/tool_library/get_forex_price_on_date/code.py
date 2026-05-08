import pandas as pd

from typing import Any, Dict, Union

from ..utils import _get_and_clean_forex_data, _log_debug


def get_forex_price_on_date(
    symbol: str,
    query_date: str
) -> Union[Dict[str, Any], str]:
    """
    获取【单个外汇品种】在【某一个指定日期】的（最近）有效行情数据。
    [原子化工具]
    
    注意: 此函数将返回指定日期 'YYYY-MM-DD' *或* 在此之前的 *最近一个* 有效数据点。
    
    :param symbol: 要查询的品种代码。例如: 'USDCNH', 'EURCNH'。
    :param query_date: 要查询的日期, 格式 'YYYY-MM-DD'.
    :return: 一个包含该日期行情数值的字典, 或一个错误信息字符串。
    """
    _log_debug(f"--- [数据获取] 正在获取 '{symbol}' 在 {query_date} (或之前) 的数据... ---")
    df_or_error = _get_and_clean_forex_data(symbol)
    if isinstance(df_or_error, str):
        _log_debug(f"--- [数据获取] 内部函数返回错误: {df_or_error} ---")
        return df_or_error  
    df = df_or_error
    try:
        data_series = df.asof(query_date)
        if data_series is None or pd.isna(data_series).all():
            error_message = f"错误：在 {query_date} 或此日期之前没有找到 '{symbol}' 的任何数据。"
            _log_debug(f"--- [数据获取] {error_message} ---")
            return error_message
        result_dict = data_series.to_dict()
        result_dict['symbol'] = symbol 
        result_dict['query_date'] = query_date
        result_dict['actual_date'] = data_series.name.strftime('%Y-%m-%d') 
        if '日期' in result_dict:
            del result_dict['日期']
        return result_dict
    except Exception as e:
        error_message = f"错误: 筛选日期 {query_date} 时出错: {e}。请检查日期格式是否为 'YYYY-MM-DD'。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
