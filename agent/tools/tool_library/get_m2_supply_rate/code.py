import pandas as pd

from typing import Union

from ..utils import _get_and_clean_m2_data, _log_debug


def get_m2_supply_rate(
start_date: str, end_date: str
) -> Union[pd.DataFrame, str]:
    """
    获取中国M2货币供应年率在【指定时间段内】的月度数据。
    
    :param start_date: 开始日期, 格式 'YYYY-MM'.
    :param end_date: 结束日期, 格式 'YYYY-MM'.
    :return: 一个包含'date' (月份) 和 'value' (M2年率) 列的DataFrame, 或一个错误信息字符串。
    """
    _log_debug(f"--- [数据获取] 正在获取 M2供应年率 从 {start_date} 到 {end_date} 的数据... ---")
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
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        filtered_df = df.loc[mask]
    except Exception as e:
        error_message = f"错误：在筛选日期 {start_date} 到 {end_date} 时发生错误: {e}。请检查日期格式是否为 YYYY-MM。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
    if filtered_df.empty:
        error_message = f"错误：在 {start_date} 到 {end_date} 的时间范围内没有找到 M2 数据。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
    return filtered_df
