import pandas as pd

from typing import Any, Dict, Union

from ..utils import _get_and_clean_currency_data, _log_debug


def get_currency_rate_on_date(
currency_name: str,
    query_date: str
) -> Union[Dict[str, Any], str]:
    """
    获取【某种外币】对人民币汇率中间价在【某一个指定日期】的（最近）有效数值。
    
    注意: 此函数将返回指定日期 'YYYY-MM-DD' *或* 在此之前的 *最近一个* 有效数据点。
    
    :param currency_name: 要查询的货币名称。必须是数据接口支持的币种之一，例如 "美元", "欧元", "日元" 等。
    :param query_date: 要查询的日期, 格式 'YYYY-MM-DD'.
    :return: 一个包含该日期汇率数值的字典, 或一个错误信息字符串。
    """
    _log_debug(f"--- [数据获取] 正在获取 '{currency_name}' 在 {query_date} (或之前) 的汇率数据... ---")
    df_or_error = _get_and_clean_currency_data()
    if isinstance(df_or_error, str):
        _log_debug(f"--- [数据获取] 内部函数返回错误: {df_or_error} ---")
        return df_or_error  
    df = df_or_error
    if df.empty:
        error_message = "错误：汇率数据获取成功，但未返回任何数据。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
    if currency_name not in df.columns:
        valid_currencies = [col for col in df.columns if '代码' not in col] 
        error_message = f"错误: 无效的货币名称 '{currency_name}'。有效选项包括: {valid_currencies}"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
    try:
        data_series = df.asof(query_date)
        if data_series is None or pd.isna(data_series).all():
            error_message = f"错误：在 {query_date} 或此日期之前没有找到任何汇率数据。"
            _log_debug(f"--- [数据获取] {error_message} ---")
            return error_message
        value = data_series[currency_name]
        actual_date = data_series.name.strftime('%Y-%m-%d') 
        if pd.isna(value):
            error_message = f"错误：在 {actual_date} 找到了数据行，但货币 '{currency_name}' 的值为NaN。"
            _log_debug(f"--- [数据获取] {error_message} ---")
            return error_message
        result_dict = {
            "currency_name": currency_name,
            "query_date": query_date,   
            "actual_date": actual_date, 
            "value": value
        }
        return result_dict
    except Exception as e:
        error_message = f"错误: 筛选日期 {query_date} 时出错: {e}。请检查日期格式是否为 'YYYY-MM-DD'。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
