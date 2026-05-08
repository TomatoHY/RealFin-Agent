import pandas as pd

from typing import Union

from ..utils import _log_debug


def calculate_lpr_rate_change(
indicator_name: str,
    start_date: str,
    end_date: str
) -> Union[pd.DataFrame, str]:
    """
    计算某个LPR利率品种在【指定时间段内】的变化值（单位：基点）。
    
    :param indicator_name: 要分析的利率品种名称。必须是 "LPR1Y", "LPR5Y", "RATE_1", "RATE_2" 之一。
    :param start_date: 开始日期, 格式 'YYYY-MM-DD'.
    :param end_date: 结束日期, 格式 'YYYY-MM-DD'.
    :return: 一个包含利率变化详情的DataFrame, 或一个错误信息字符串。
    """
    _log_debug(f"--- [分析任务] 正在计算 '{indicator_name}' 从 {start_date} 到 {end_date} 的变化... ---")
    df_or_error = get_lpr_rate(indicator_name, start_date, end_date)
    if isinstance(df_or_error, str):
        _log_debug(f"--- [分析任务] 内部数据获取失败: {df_or_error} ---")
        return df_or_error  
    filtered_df = df_or_error
    if len(filtered_df) < 2:
        error_message = f"错误: 在时间范围 {start_date} 到 {end_date} 内数据点不足 (少于2个)，无法计算变化。"
        _log_debug(f"--- [分析任务] {error_message} ---")
        return error_message 
    try:
        start_data = filtered_df.iloc[0]
        end_data = filtered_df.iloc[-1]
        start_value = start_data[indicator_name]
        end_value = end_data[indicator_name]
        basis_point_change = (end_value - start_value) * 100
    except KeyError as e:
        error_message = f"错误：在分析数据时缺少必要的列: {e}。"
        _log_debug(f"--- [分析任务] {error_message} ---")
        return error_message
    except Exception as e:
        error_message = f"错误：在计算变化时发生未知错误: {e}。"
        _log_debug(f"--- [分析任务] {error_message} ---")
        return error_message
    result_data = {
        "指标名称": [indicator_name],
        "开始时间": [start_data['日期'].strftime('%Y-%m-%d')],
        "开始数值(%)": [start_value],
        "结束时间": [end_data['日期'].strftime('%Y-%m-%d')],
        "结束数值(%)": [end_value],
        "变化(基点)": [int(basis_point_change)]
    }
    return pd.DataFrame(result_data)
