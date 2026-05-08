import pandas as pd

from typing import Any, Dict, Union

from ..utils import _get_and_clean_m2_data, _log_debug


def get_m2_supply_rate_on_date(
query_date: str
) -> Union[Dict[str, Any], str]:
    """
    获取中国M2货币供应年率在【某一个指定月份】的（最近）有效数值。
    
    注意: 此函数将返回指定月份 'YYYY-MM' *或* 在此之前的 *最近一个* 有效数据点。
    
    :param query_date: 要查询的月份, 格式 'YYYY-MM'.
    :return: 一个包含该月份M2年率数值的字典, 或一个错误信息字符串。
    """
    _log_debug(f"--- [数据获取] 正在获取 M2供应年率 在 {query_date} (或之前) 的月度数据... ---")
    df_or_error = _get_and_clean_m2_data()
    if isinstance(df_or_error, str):
        _log_debug(f"--- [数据获取] 内部函数返回错误: {df_or_error} ---")
        return df_or_error 
    df = df_or_error
    if df.empty:
        error_message = "错误：M2数据获取成功，但未返回任何数据。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
    try:
        filtered_df = df[df['date'] <= query_date]
        if filtered_df.empty:
            error_message = f"错误：在 {query_date} 或此日期之前没有找到任何M2数据。"
            _log_debug(f"--- [数据获取] {error_message} ---")
            return error_message
        data_series = filtered_df.iloc[-1]
        value = data_series['value']
        actual_date = data_series['date'] 
        if pd.isna(value):
            error_message = f"错误：在 {actual_date} 找到了数据行，但 'value' (M2年率) 的值为NaN。"
            _log_debug(f"--- [数据获取] {error_message} ---")
            return error_message
        result_dict = {
            "indicator_name": "M2货币供应年率",
            "query_date": query_date,   
            "actual_date": actual_date, 
            "value": value
        }
        return result_dict
    except Exception as e:
        error_message = f"错误: 筛选日期 {query_date} 时出错: {e}。请检查日期格式是否为 'YYYY-MM'。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
