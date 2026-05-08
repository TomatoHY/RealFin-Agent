import pandas as pd

from typing import Any, Dict, Union

from ..utils import _get_and_clean_lpr_data, _log_debug


def get_lpr_rate_on_date(
indicator_name: str,
    query_date: str
) -> Union[Dict[str, Any], str]:
    """
    获取LPR（贷款市场报价利率）在【某一个指定日期】的（最近）有效数值。
    
    注意: 此函数将返回指定日期 *或* 在此之前的 *最近一个* 有效数据点。
    
    :param indicator_name: 要查询的利率品种名称。必须是 "LPR1Y", "LPR5Y", "RATE_1", "RATE_2" 之一。
    :param query_date: 要查询的日期, 格式 'YYYY-MM-DD'.
    :return: 一个包含该日期利率数值的字典, 或一个错误信息字符串。
    """
    _log_debug(f"--- [数据获取] 正在获取 '{indicator_name}' 在 {query_date} (或之前) 的数据... ---")
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
    if indicator_name not in df.columns:
        error_message = f"错误：LPR数据源中未找到指标 '{indicator_name}'。可用指标: {df.columns.tolist()}"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
    try:
        data_series = df.asof(query_date)
        if data_series is None or pd.isna(data_series).all():
            error_message = f"错误：在 {query_date} 或此日期之前没有找到任何LPR数据。"
            _log_debug(f"--- [数据获取] {error_message} ---")
            return error_message
        value = data_series[indicator_name]
        actual_date = data_series.name.strftime('%Y-%m-%d') 
        if pd.isna(value):
            error_message = f"错误：在 {actual_date} 找到了数据行，但指标 '{indicator_name}' 的值为NaN。"
            _log_debug(f"--- [数据获取] {error_message} ---")
            return error_message
        result_dict = {
            "indicator_name": indicator_name,
            "query_date": query_date,
            "actual_date": actual_date,
            "value": value
        }
        return result_dict
    except Exception as e:
        error_message = f"错误: 筛选日期 {query_date} 时出错: {e}。请检查日期格式是否为 'YYYY-MM-DD'。"
        _log_debug(f"--- [数据获取] {error_message} ---")
        return error_message
