import json

from datetime import datetime
from typing import Optional

from ..get_code_from_name.code import get_code_from_name
from ..get_a_stock_daily_price.code import get_a_stock_daily_price
from ..get_hk_stock_daily_price.code import get_hk_stock_daily_price
from ..get_us_stock_daily_price.code import get_us_stock_daily_price
from ..utils import _log_debug


def calculate_price_change_pct_in_period(
start_date: str,
    end_date: str,
    market: str,
    adjust: str = 'qfq',
    name: Optional[str] = None,
    code: Optional[str] = None
) -> str:
    """
    计算单只股票在【指定时间段内】的累计涨跌幅（百分比）。
    """
    if not code and not name:
        return "错误：必须提供股票代码 (code) 或股票名称 (name)。"
    if adjust not in ['', 'qfq', 'hfq']:
        return f"错误: 'adjust' 参数 '{adjust}' 无效。有效选项: '', 'qfq', 'hfq'。"
    try:
        start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return f"错误: 日期格式无效。请确保 start_date 和 end_date 均为 'YYYY-MM-DD' 格式。"
    if start_date_dt >= end_date_dt:
        return f"错误: 开始日期 {start_date} 必须早于结束日期 {end_date}。"
    effective_code = code
    effective_name = name
    if not effective_code and name:
        _log_debug(f"--- [代码解析] 缺少代码，正在尝试通过名称 '{name}' (市场: {market}) 查找代码... ---")
        effective_code = get_code_from_name(name, market=market)
        if not effective_code:
            return f"错误：通过名称 '{name}' 在市场 '{market}' 未能找到有效的股票代码。"
        _log_debug(f"--- [代码解析] 成功找到代码: {effective_code} ---")
    if not effective_code:
        return "错误：最终未能获得一个有效的股票代码用于查询。"
    history_fetcher_map = {
        'a': get_a_stock_daily_price,
        'hk': get_hk_stock_daily_price,
        'us': get_us_stock_daily_price
    }
    if market not in history_fetcher_map:
        return f"错误：无效的市场类型 '{market}'。支持的市场: 'a', 'hk', 'us'。"
    history_fetcher = history_fetcher_map[market]
    _log_debug(f"--- 正在获取代码 {effective_code} 从 {start_date} 到 {end_date} 的历史收盘价... ---")
    try:
        hist_data_str = history_fetcher(
            code=effective_code,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        hist_data_list = json.loads(hist_data_str)
        if not isinstance(hist_data_list, list) or not hist_data_list:
            return f"错误: 在指定时间段内未能获取到代码'{effective_code}'的任何交易数据。底层工具返回: {hist_data_str}"
        first_day_data = hist_data_list[0]
        last_day_data = hist_data_list[-1]
        start_price = float(first_day_data['close'])
        end_price = float(last_day_data['close'])
        actual_start_date = first_day_data['date']
        actual_end_date = last_day_data['date']
    except (json.JSONDecodeError, TypeError):
        return f"错误：解析代码'{effective_code}'的历史数据时失败。底层工具返回的不是有效的JSON列表: {hist_data_str}"
    except (IndexError, KeyError, ValueError) as e:
        return f"错误：返回的历史数据格式不正确，无法提取首末日期或收盘价。底层工具返回: {hist_data_str} (错误: {e})"
    except Exception as e:
        return f"错误：获取代码'{effective_code}'的历史数据时发生未知错误: {e}。底层工具返回: {hist_data_str}"
    try:
        if start_price == 0:
            return f"错误: 计算错误，起始交易日 ({actual_start_date}) 的收盘价为0，无法计算涨跌幅。"
        change_pct = ((end_price - start_price) / start_price) * 100
        result_json = {
            "analysis_type": "stock_change_percentage_in_period",
            "stock_identifier": effective_name or effective_code, 
            "stock_code": effective_code,
            "market": market,
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
        return result_json
    except Exception as e:
        return f"错误：在计算累计涨跌幅时发生未知异常: {e}"
