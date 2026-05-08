from datetime import datetime, timedelta
from typing import Optional, Any, Dict

from ..get_code_from_name.code import get_code_from_name
from ..get_a_stock_daily_price.code import get_a_stock_daily_price
from ..get_hk_stock_daily_price.code import get_hk_stock_daily_price
from ..get_us_stock_daily_price.code import get_us_stock_daily_price
from ..utils import LATEST_KEYWORDS, _log_debug, _parse_price_and_date_from_output


def calculate_price_change_pct(
query_date: str,
    market: str,
    adjust: str = 'qfq',
    name: Optional[str] = None,
    code: Optional[str] = None,
    original_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    计算单只股票在特定日期的涨跌幅。
    """
    def _fail(error_msg: str) -> Dict[str, Any]:
        return {
            "calculation_result": {
                "percentage_change": error_msg
            }
        }
    if not code and not name:
        return _fail("错误：必须提供股票代码 (code) 或股票名称 (name)。")
    effective_code = code
    if not effective_code and name:
        _log_debug(f"--- [代码解析] 缺少代码，正在尝试通过名称 '{name}' 查找代码... ---")
        try:
            resolved_code = get_code_from_name(name=name, market=market) 
            if not resolved_code or isinstance(resolved_code, str) and "--- [LocalSearch] 查找" in resolved_code:
                return _fail(f"错误：get_code_from_name 未能解析 '{name}'。返回: {resolved_code}")
            effective_code = resolved_code 
            _log_debug(f"--- [代码解析] 成功找到代码: {effective_code} ---")
        except Exception as e:
            return _fail(f"错误：在为 '{name}' 解析代码时失败: {e}")
    if not effective_code:
        return _fail("错误：最终未能获得一个有效的股票代码用于查询。")
    price_fetcher_map = {'a': get_a_stock_daily_price, 'hk': get_hk_stock_daily_price, 'us': get_us_stock_daily_price}
    if market not in price_fetcher_map:
        return _fail(f"错误：无效的市场类型 '{market}'。支持的市场: 'a', 'hk', 'us'。")
    price_fetcher = price_fetcher_map[market]
    effective_query_date = query_date
    if original_query and any(keyword in original_query.lower() for keyword in LATEST_KEYWORDS):
        today_str = datetime.now().strftime('%Y-%m-%d')
        if query_date != today_str:
            _log_debug(f"--- [意图感知] 检测到关键词。将忽略'{query_date}'，强制使用今天'{today_str}'查询。---")
        effective_query_date = today_str
    if query_date.lower().strip() in LATEST_KEYWORDS:
        effective_query_date = 'latest' 
    _log_debug(f"--- 正在获取 {effective_query_date} (T日) 的收盘价... ---")
    current_close_output = price_fetcher(
        query_date=effective_query_date, column_label='close', adjust=adjust,
        name=name, code=effective_code, original_query=original_query
    )
    current_close_price, actual_date_str = _parse_price_and_date_from_output(current_close_output)
    if current_close_price is None:
        return _fail(f"错误: 无法获取 {effective_query_date} 的收盘价。底层工具返回: {current_close_output}")
    if actual_date_str is None:
        return _fail(f"错误: 无法从 '{current_close_output}' 中解析出实际数据日期。")
    date_part_only = actual_date_str.split(' ')[0]
    try:
        prev_date_dt = datetime.strptime(date_part_only, '%Y-%m-%d') - timedelta(days=1)
    except ValueError as e:
        return _fail(f"错误: 无法解析T日日期 '{date_part_only}': {e}")
    _log_debug(f"--- 正在查找 {actual_date_str} 前一交易日 (T-1) 的收盘价... ---")
    previous_close_output = price_fetcher(
        query_date=prev_date_dt.strftime('%Y-%m-%d'), column_label='close', adjust=adjust,
        name=name, code=effective_code
    )
    previous_close_price, prev_actual_date_str = _parse_price_and_date_from_output(previous_close_output)
    if previous_close_price is None:
        return _fail(f"错误: 无法获取 {actual_date_str} 之前交易日的收盘价。底层工具返回: {previous_close_output}")
    if prev_actual_date_str is None:
        prev_actual_date_str = "未知" 
    try:
        if previous_close_price == 0:
            return _fail(f"错误: Calculation Error, 前一交易日收盘价为0，无法计算涨跌幅。")
        price_change_value = current_close_price - previous_close_price
        price_change_pct = (price_change_value / previous_close_price) * 100
        result_json = {
            "analysis_type": "stock_change_percentage",
            "stock_identifier": name or effective_code,
            "market": market,
            "query_date": query_date,
            "current_day": {
                "date": actual_date_str,
                "close_price": f"{current_close_price:.2f}"
            },
            "previous_day": {
                "date": prev_actual_date_str,
                "close_price": f"{previous_close_price:.2f}"
            },
            "calculation_result": {
                "price_change": f"{price_change_value:+.2f}",
                "percentage_change": f"{price_change_pct:+.2f}%" 
            }
        }
        return result_json
    except Exception as e:
        return _fail(f"错误：在计算涨跌幅时发生未知异常: {e}")
