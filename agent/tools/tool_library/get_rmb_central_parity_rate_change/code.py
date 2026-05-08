import akshare as ak
import pandas as pd

from typing import Union, List

from ..utils import _log_debug


def get_rmb_central_parity_rate_change(
    start_date: str, 
    end_date: str, 
    currencies: List[str]
) -> Union[pd.DataFrame, str]:
    """
    获取并计算指定日期范围内、特定币种的人民币汇率中间价每日涨跌幅。

    Args:
        start_date (str): 查询的开始日期，格式应为 'YYYY-MM-DD'。
        end_date (str): 查询的结束日期，格式应为 'YYYY-MM-DD'。
        currencies (List[str]): 一个包含所需货币标准名称的列表。
                                例如: ['美元', '欧元', '泰铢']。

    Returns:
        Union[pd.DataFrame, str]: 
            - 成功: 一个包含指定货币在指定日期范围内每日涨跌幅的DataFrame。
            - 失败: 一个包含错误信息的字符串。                      
    注意:
        - 正值表示当日汇率数值升高，负值表示降低。
        - 其经济学含义需根据标价法解释。
    """
    if not isinstance(currencies, list) or not currencies:
        return "错误：'currencies' 参数必须是一个非空的列表，例如 ['美元', '欧元']。"
    try:
        pd.to_datetime(start_date)
        pd.to_datetime(end_date)
    except ValueError:
        return "错误：日期格式不正确，请使用 'YYYY-MM-DD' 格式。"
    try:
        currency_df = ak.currency_boc_safe()
        if currency_df.empty:
            error_message = "错误：API (ak.currency_boc_safe) 调用成功，但未返回任何数据。"
            _log_debug(f"--- [汇率涨跌幅] {error_message} ---")
            return error_message
        currency_df['日期'] = pd.to_datetime(currency_df['日期'])
        currency_df = currency_df.set_index('日期').sort_index()
        valid_currencies = [c for c in currencies if c in currency_df.columns]
        missing_currencies = [c for c in currencies if c not in currency_df.columns]
        if missing_currencies:
            _log_debug(f"警告：以下货币名称无法找到，将被忽略: {', '.join(missing_currencies)}")
        if not valid_currencies:
            available_currencies = [c for c in currency_df.columns if '代码' not in c]
            error_message = f"错误：您输入的所有货币名称 {currencies} 都不在可用列表中。可用选项（部分）: {available_currencies[:10]}..."
            _log_debug(f"--- [汇率涨跌幅] {error_message} ---")
            return error_message
        filtered_df = currency_df[valid_currencies].copy()
        for col in filtered_df.columns:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')
        daily_change_df = filtered_df.pct_change() * 100
        final_df = daily_change_df.loc[start_date:end_date].copy()
        final_df.columns = [f"{col}_涨跌幅" for col in final_df.columns]
        final_df.dropna(how='all', inplace=True)
        if final_df.empty:
            error_message = f"错误：在 {start_date} 到 {end_date} 的时间范围内没有找到您所选货币 {valid_currencies} 的任何涨跌幅数据。"
            _log_debug(f"--- [汇率涨跌幅] {error_message} ---")
            return error_message
        return final_df
    except Exception as e:
        error_message = f"错误：[汇率涨跌幅] 处理过程中发生未知错误: {e}"
        _log_debug(error_message)
        return error_message
