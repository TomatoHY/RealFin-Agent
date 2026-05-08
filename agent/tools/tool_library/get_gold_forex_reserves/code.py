import pandas as pd

from typing import Union

from ..utils import _get_and_clean_gold_forex_data, _log_debug


def get_gold_forex_reserves(
    indicator_name: str,
    start_date: str,
    end_date: str
) -> Union[pd.DataFrame, str]:
    """
    获取央行黄金储备或国家外汇储备在【指定时间段内】的月度数据。
    
    :param indicator_name: 要查询的指标名称。必须是 "黄金储备" 或 "国家外汇储备" 之一。
    :param start_date: 开始日期, 格式 'YYYY-MM'.
    :param end_date: 结束日期, 格式 'YYYY-MM'.
    :return: 一个包含'统计时间'和指定指标列的DataFrame。
    """
    _log_debug(f"--- [数据获取] 正在获取 '{indicator_name}' 从 {start_date} 到 {end_date} 的数据... ---")
    VALID_INDICATORS = ["黄金储备", "国家外汇储备"]
    if indicator_name not in VALID_INDICATORS:
        error_message = f"错误: 无效的指标名称 '{indicator_name}'。有效选项: {VALID_INDICATORS}"
        _log_debug(f"错误: 无效的指标名称 '{indicator_name}'。有效选项: {VALID_INDICATORS}")
        return error_message
    df_or_error = _get_and_clean_gold_forex_data()
    if isinstance(df_or_error, str):
        _log_debug(f"--- [数据获取] 内部函数返回错误: {df_or_error} ---")
        return df_or_error  # 直接将内部错误信息透传出去
    df = df_or_error
    if df.empty:
        error_message = "错误：数据获取成功，但未返回任何数据。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
    try:
        mask = (df['统计时间'] >= start_date) & (df['统计时间'] <= end_date)
        filtered_df = df.loc[mask]
    except Exception as e:
        error_message = f"错误：在筛选日期 {start_date} 到 {end_date} 时发生错误: {e}。请检查日期格式是否为 YYYY-MM。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
    if filtered_df.empty:
        error_message = f"错误：在 {start_date} 到 {end_date} 的时间范围内没有找到 '{indicator_name}' 的数据。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
    try:
        return filtered_df[['统计时间', indicator_name]]
    except KeyError:
        error_message = f"错误：数据中未找到列 '{indicator_name}'。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
