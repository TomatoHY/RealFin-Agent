import pandas as pd

from typing import Union

from ..utils import _get_and_clean_currency_data, _log_debug


def get_monthly_avg_currency_rate(
currency_name: str,
    start_date: str,
    end_date: str
) -> Union[pd.DataFrame, str]:
    """
    计算【某种外币】对人民币汇率中间价在【指定时间段内】的【月度算术平均值】。
    
    :param currency_name: 要查询的货币名称。必须是数据接口支持的币种之一，例如 "美元", "欧元", "日元" 等。
    :param start_date: 开始日期, 格式 'YYYY-MM-DD'.
    :param end_date: 结束日期, 格式 'YYYY-MM-DD'.
    :return: 一个包含'月份'和该货币月度平均汇率列的DataFrame, 或一个错误信息字符串。
    """
    _log_debug(f"--- [月度平均计算] 正在计算 '{currency_name}' 从 {start_date} 到 {end_date} 的月度平均汇率... ---")
    df_or_error = _get_and_clean_currency_data()
    if isinstance(df_or_error, str):
        _log_debug(f"--- [月度平均计算] 内部函数返回错误: {df_or_error} ---")
        return df_or_error  
    df = df_or_error
    if df.empty:
        error_message = "错误：汇率数据获取成功，但未返回任何数据。"
        _log_debug(f"--- [月度平均计算] {error_message} ---")
        return error_message
    if currency_name not in df.columns:
        valid_currencies = [col for col in df.columns if '代码' not in col] 
        error_message = f"错误: 无效的货币名称 '{currency_name}'。有效选项包括: {valid_currencies}"
        _log_debug(f"--- [月度平均计算] {error_message} ---")
        return error_message 
    try:
        filtered_df = df.loc[start_date:end_date]
    except Exception as e:
        error_message = f"错误: 筛选日期范围 {start_date} 到 {end_date} 时出错: {e}。请检查日期格式是否为 'YYYY-MM-DD'。"
        _log_debug(f"--- [月度平均计算] {error_message} ---")
        return error_message
    if filtered_df.empty:
        error_message = f"错误: 在时间范围 {start_date} 到 {end_date} 内没有找到 '{currency_name}' 的任何数据。"
        _log_debug(f"--- [月度平均计算] {error_message} ---")
        return error_message
    try:
        monthly_avg = filtered_df[currency_name].resample('M').mean()
        if monthly_avg.isnull().all():
            error_message = f"错误: 在 {start_date} 到 {end_date} 期间, '{currency_name}' 的数据全部无效 (NaN)，无法计算月度平均值。"
            _log_debug(f"--- [月度平均计算] {error_message} ---")
            return error_message
        monthly_avg.dropna(inplace=True)
    except Exception as e:
        error_message = f"错误: 在计算 '{currency_name}' 的月度平均值时发生错误: {e}"
        _log_debug(f"--- [月度平均计算] {error_message} ---")
        return error_message
    result_df = monthly_avg.reset_index()
    result_df.rename(columns={'日期': '月份', currency_name: f'{currency_name}_月度平均值'}, inplace=True)
    result_df['月份'] = result_df['月份'].dt.strftime('%Y-%m')
    return result_df
