import pandas as pd

from typing import Union

from ..utils import _get_and_clean_lpr_data, _log_debug


def get_lpr_rate(
indicator_name: str,
    start_date: str,
    end_date: str
) -> Union[pd.DataFrame, str]:
    """
    获取LPR（贷款市场报价利率）或其他相关贷款利率在【指定时间段内】的历史数据。
    
    :param indicator_name: 要查询的利率品种名称。必须是 "LPR1Y", "LPR5Y", "RATE_1", "RATE_2" 之一。
    :param start_date: 开始日期, 格式 'YYYY-MM-DD'.
    :param end_date: 结束日期, 格式 'YYYY-MM-DD'.
    :return: 一个包含'日期'和指定利率品种数值列的DataFrame, 或一个错误信息字符串。
    """
    _log_debug(f"--- [数据获取] 正在获取 '{indicator_name}' 从 {start_date} 到 {end_date} 的数据... ---")
    VALID_INDICATORS = ["LPR1Y", "LPR5Y", "RATE_1", "RATE_2"]
    if indicator_name not in VALID_INDICATORS:
        error_message = f"错误: 无效的指标名称 '{indicator_name}'。有效选项: {VALID_INDICATORS}"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message 
    df_or_error = _get_and_clean_lpr_data()
    if isinstance(df_or_error, str):
        _log_debug(f"--- [数据获取] 内部函数返回错误: {df_or_error} ---")
        return df_or_error  
    df = df_or_error
    if df.empty:
        error_message = "错误：LPR数据获取成功，但未返回任何数据。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
    try:
        if indicator_name not in df.columns:
            error_message = f"错误：LPR数据源中未找到指标 '{indicator_name}'。可用指标: {df.columns.tolist()}"
            _log_debug(f"--- [数据获取] {error_message} ---")
            return error_message
        filtered_df = df.loc[start_date:end_date, [indicator_name]].dropna().reset_index()
        filtered_df.rename(columns={'TRADE_DATE': '日期'}, inplace=True)
    except Exception as e:
        error_message = f"错误: 筛选时出错（日期 {start_date} 到 {end_date} 或指标 '{indicator_name}'）。请检查日期格式是否为 'YYYY-MM-DD'。错误详情: {e}"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message 
    if filtered_df.empty:
        error_message = f"错误：在 {start_date} 到 {end_date} 的时间范围内没有找到 '{indicator_name}' 的数据。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
    return filtered_df
