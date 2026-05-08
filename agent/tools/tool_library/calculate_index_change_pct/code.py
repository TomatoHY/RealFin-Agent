from datetime import datetime, timedelta
from typing import Any, Dict

from ..utils import LATEST_KEYWORDS, _log_debug, _parse_index_price_from_output


def calculate_index_change_pct(
identifier: str,
    market: str,
    query_date: str = "latest"
) -> Dict[str, Any]:
    """
    计算指数在特定日期的涨跌幅。
    """
    def _fail(error_msg: str) -> Dict[str, Any]:
        return {
            "result": { 
                "percentage_change": error_msg
            }
        }
    is_latest_query = (query_date and query_date.lower().strip() in LATEST_KEYWORDS)
    _log_debug(f"--- 正在获取 {identifier} (T日) 的收盘价... ---")
    if is_latest_query:
        current_close_output = get_index_realtime(
            identifier=identifier,
            column_label='close',
            market=market
        )
    else:
        current_close_output = get_index_history(
            identifier=identifier,
            column_label='close',
            query_date=query_date,
            market=market
        )
    current_close_price, actual_date_str = _parse_index_price_from_output(current_close_output)
    if current_close_price is None:
        return _fail(f"错误: 无法获取 {identifier} (T日) 的收盘价。底层工具返回: {current_close_output.get('value')}")
    if actual_date_str is None:
        return _fail(f"错误: 无法从 '{current_close_output}' 中解析出实际数据日期(T日)。")
    date_part_only = actual_date_str.split(' ')[0]
    try:
        prev_date_dt = datetime.strptime(date_part_only, '%Y-%m-%d') - timedelta(days=1)
        prev_date_str = prev_date_dt.strftime('%Y-%m-%d')
    except ValueError as e:
        return _fail(f"错误: 无法解析T日日期 '{date_part_only}': {e}")
    _log_debug(f"--- 正在查找 {actual_date_str} 前一交易日 (T-1, 即 {prev_date_str}) 的收盘价... ---")
    previous_close_output = get_index_history(
        identifier=identifier,
        column_label='close',
        query_date=prev_date_str, 
        market=market
    )
    previous_close_price, prev_actual_date_str = _parse_index_price_from_output(previous_close_output)
    if previous_close_price is None:
        return _fail(f"错误: 无法获取 {actual_date_str} 之前交易日(T-1)的收盘价。底层工具返回: {previous_close_output.get('value')}")
    if prev_actual_date_str is None:
        prev_actual_date_str = "未知" 
    try:
        if previous_close_price == 0:
            return _fail(f"错误: Calculation Error, T-1日收盘价为0，无法计算涨跌幅。")
        
        price_change_value = current_close_price - previous_close_price
        price_change_pct = (price_change_value / previous_close_price) * 100
        result_json = {
            "result": { 
                "price_change": f"{price_change_value:+.2f}",
                "percentage_change": f"{price_change_pct:+.2f}%" 
            },
            "analysis_type": "index_change_percentage",
            "identifier": identifier,
            "market": market,
            "current_day": {
                "date": actual_date_str,
                "close_price": f"{current_close_price:.2f}"
            },
            "previous_day": {
                "date": prev_actual_date_str,
                "close_price": f"{previous_close_price:.2f}"
            }
        }
        return result_json
    except Exception as e:
        return _fail(f"错误：在计算涨跌幅时发生未知异常: {e}")
