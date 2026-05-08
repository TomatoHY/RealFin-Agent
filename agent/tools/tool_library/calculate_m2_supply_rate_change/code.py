import pandas as pd

from typing import Union

from ..utils import _get_and_clean_m2_data, _log_debug


def calculate_m2_supply_rate_change(
start_date: str, 
    end_date: str
) -> Union[pd.DataFrame, str]:
    """
    【分析工具】计算中国M2货币供应年率在【指定时间段内】的变化情况（绝对值变化）。
    
    :param start_date: 开始日期, 格式 'YYYY-MM'.
    :param end_date: 结束日期, 格式 'YYYY-MM'.
    :return: 一个包含M2年率变化详情的DataFrame, 或一个错误信息字符串。
    """
    _log_debug(f"--- [分析任务] 正在计算 M2供应年率 从 {start_date} 到 {end_date} 的变化... ---")
    df_or_error = _get_and_clean_m2_data()
    if isinstance(df_or_error, str):
        _log_debug(f"--- [分析任务] 内部函数返回错误: {df_or_error} ---")
        return df_or_error  
    df = df_or_error
    if df.empty:
        error_message = "错误：M2数据获取成功，但未返回任何数据。"
        _log_debug(f"--- [分析任务] {error_message} ---")
        return error_message
    try:
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        filtered_df = df.loc[mask]
    except Exception as e:
        error_message = f"错误：在筛选日期 {start_date} 到 {end_date} 时发生错误: {e}。请检查日期格式是否为 YYYY-MM。"
        _log_debug(f"--- [分析任务] {error_message} ---")
        return error_message
    if len(filtered_df) < 2:
        error_message = f"错误: 在时间范围 {start_date} 到 {end_date} 内数据点不足 (少于2个)，无法计算变化。"
        _log_debug(f"--- [分析任务] {error_message} ---")
        return error_message
    try:
        start_data = filtered_df.iloc[0]
        end_data = filtered_df.iloc[-1]
        start_value = start_data['value']
        end_value = end_data['value']
        absolute_change = end_value - start_value
    except KeyError as e:
        error_message = f"错误：数据中缺少必要的 'value' 列: {e}。"
        _log_debug(f"--- [分析任务] {error_message} ---")
        return error_message
    except Exception as e:
        error_message = f"错误：在计算变化时发生未知错误: {e}。"
        _log_debug(f"--- [分析任务] {error_message} ---")
        return error_message
    result_data = {
        "指标名称": ["M2货币供应年率 (%)"],
        "开始时间": [start_data['date']],
        "开始数值": [start_value],
        "结束时间": [end_data['date']],
        "结束数值": [end_value],
        "绝对变化(百分点)": [round(absolute_change, 2)]
    }
    return pd.DataFrame(result_data)
