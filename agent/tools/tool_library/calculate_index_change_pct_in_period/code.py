from datetime import datetime
from typing import Optional, Any, Dict, Union

from ..get_index_history import get_index_history
from ..utils import _log_debug


def calculate_index_change_pct_in_period(
identifier: str,
    start_date: str,
    end_date: str,
    market: Optional[str] = None
) -> Union[Dict[str, Any], str]:
    """
    计算单个指数在【指定时间段内】的累计涨跌幅（百分比）。
    函数会利用 get_index_history 自动查找此时间段内的第一个和最后一个实际交易日的收盘价进行计算。

    :param identifier: 指数名称或代码, 例如 "沪深300" 或 "纳斯达克"。
    :param start_date: 查询周期的开始日期 (格式 'YYYY-MM-DD')。
    :param end_date: 查询周期的结束日期 (格式 'YYYY-MM-DD')。
    :param market: 市场提示 (可选), 例如 'a', 'hk', 'us'。
    :return: 包含详细计算结果的字典，或描述错误的字符串。
    """
    _log_debug(f"--- [指数涨跌幅计算] 正在计算 '{identifier}' 从 {start_date} 到 {end_date} 的涨跌幅... ---")
    if not identifier:
        return "错误：必须提供指数的名称或代码 (identifier)。"
    try:
        start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return f"错误: 日期格式无效。请确保 start_date 和 end_date 均为 'YYYY-MM-DD' 格式。"
    if start_date_dt >= end_date_dt:
        return f"错误: 开始日期 {start_date} 必须早于结束日期 {end_date}。"
    _log_debug(f"--- 正在获取起始点 '{start_date}' 的数据... ---")
    start_data_result = get_index_history(
        identifier=identifier,
        query_date=start_date,
        column_label='close', 
        market=market
    )
    if isinstance(start_data_result, str):
        return f"错误：获取开始日数据时失败: {start_data_result}"
    try:
        start_price = float(start_data_result['value'])
        actual_start_date = start_data_result['date']
        standard_identifier = start_data_result['identifier'] 
    except (KeyError, TypeError) as e:
        return f"错误：解析开始日数据时返回的格式不正确: {start_data_result} (错误: {e})"
    _log_debug(f"--- 正在获取结束点 '{end_date}' 的数据... ---")
    end_data_result = get_index_history(
        identifier=identifier,
        query_date=end_date,
        column_label='close',
        market=market
    )
    if isinstance(end_data_result, str):
        return f"错误：获取结束日数据时失败: {end_data_result}"
    try:
        end_price = float(end_data_result['value'])
        actual_end_date = end_data_result['date']
    except (KeyError, TypeError) as e:
        return f"错误：解析结束日数据时返回的格式不正确: {end_data_result} (错误: {e})"
    try:
        if start_price == 0:
            return f"错误: 计算错误，起始交易日 ({actual_start_date}) 的收盘价为0，无法计算涨跌幅。"
        change_pct = ((end_price - start_price) / start_price) * 100
        result_dict = {
            "analysis_type": "index_change_percentage_in_period",
            "index_identifier": standard_identifier,
            "market_hint": market,
            "query_period": {
                "start": start_date,
                "end": end_date
            },
            "actual_trading_period": {
                "start_date": actual_start_date,
                "end_date": actual_end_date
            },
            "period_prices": {
                "start_price": f"{start_price:.2f}",
                "end_price": f"{end_price:.2f}"
            },
            "calculation_result": {
                "cumulative_percentage_change": f"{change_pct:+.2f}%"
            }
        }
        return result_dict
    except Exception as e:
        return f"错误：在计算累计涨跌幅时发生未知异常: {e}"
