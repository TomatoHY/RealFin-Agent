import pandas as pd

from typing import Union

from ..utils import _get_and_clean_gold_forex_data, _log_debug


def calculate_gold_forex_change(
start_date: str,
    end_date: str
) -> Union[pd.DataFrame, str]:
    """
    【分析工具】计算黄金储备和国家外汇储备在【指定时间段内】的累计涨跌幅。
    
    :param start_date: 开始日期, 格式 'YYYY-MM'.
    :param end_date: 结束日期, 格式 'YYYY-MM'.
    :return: 一个包含两个指标变化详情的DataFrame, 或一个错误信息字符串。
    """
    _log_debug(f"--- [分析任务] 正在计算黄金和外汇储备从 {start_date} 到 {end_date} 的变化... ---")
    df_or_error = _get_and_clean_gold_forex_data()
    if isinstance(df_or_error, str):
        _log_debug(f"--- [分析任务] 内部函数返回错误: {df_or_error} ---")
        return df_or_error  
    df = df_or_error
    try:
        mask = (df['统计时间'] >= start_date) & (df['统计时间'] <= end_date)
        filtered_df = df.loc[mask].sort_values('统计时间')
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
        gold_start = start_data['黄金储备']
        gold_end = end_data['黄金储备']
        gold_change_pct = ((gold_end - gold_start) / gold_start) * 100 if gold_start != 0 else float('inf')
        forex_start = start_data['国家外汇储备']
        forex_end = end_data['国家外汇储备']
        forex_change_pct = ((forex_end - forex_start) / forex_start) * 100 if forex_start != 0 else float('inf')
    except KeyError as e:
        error_message = f"错误：数据中缺少必要的列: {e}。"
        _log_debug(f"--- [分析任务] {error_message} ---")
        return error_message
    except Exception as e:
        error_message = f"错误：在计算变化时发生未知错误: {e}。"
        _log_debug(f"--- [分析任务] {error_message} ---")
        return error_message
    result_data = {
        "指标名称": ["黄金储备 (万盎司)", "国家外汇储备 (亿美元)"],
        "开始时间": [start_data['统计时间'], start_data['统计时间']],
        "开始数值": [gold_start, forex_start],
        "结束时间": [end_data['统计时间'], end_data['统计时间']],
        "结束数值": [gold_end, forex_end],
        "变化百分比(%)": [round(gold_change_pct, 2), round(forex_change_pct, 2)]
    }
    return pd.DataFrame(result_data)
