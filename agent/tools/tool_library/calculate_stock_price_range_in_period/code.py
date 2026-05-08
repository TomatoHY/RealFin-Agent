import akshare as ak

from datetime import datetime
from typing import Optional

from ..get_code_from_name.code import get_code_from_name
from ..utils import _log_debug


def calculate_stock_price_range_in_period(
start_date: str,
    end_date: str,
    adjust: str,
    name: Optional[str] = None,
    code: Optional[str] = None
) -> str:
    """
    计算A股某只股票在【指定时间段内】的最高价与最低价之差。
    """
    if adjust not in ['', 'qfq', 'hfq']:
        return f"错误: 'adjust' 参数 '{adjust}' 无效。有效选项: '', 'qfq', 'hfq'。"
    if not code and not name:
        return "错误：必须提供股票代码 (code) 或股票名称 (name)。"
    try:
        start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_date_ak = start_date_dt.strftime('%Y%m%d')
        end_date_ak = end_date_dt.strftime('%Y%m%d')
    except ValueError:
        return f"错误: 日期格式无效。请确保 start_date 和 end_date 均为 'YYYY-MM-DD' 格式。"
    symbol = code if code else get_code_from_name(name, market='a')
    if not symbol:
        return f"错误：未能通过名称 '{name}' 或代码 '{code}' 找到对应的A股代码。"
    try:
        _log_debug(f"--- 正在为代码'{symbol}'下载从 {start_date} 到 {end_date} 的【A股】历史数据... ---")
        hist_df = ak.stock_zh_a_hist_tx(
            symbol=symbol,
            adjust=adjust,
            start_date=start_date_ak,
            end_date=end_date_ak
        )
        if hist_df is None or hist_df.empty:
            return f"错误: 在指定时间段内未能获取到代码'{symbol}'的任何交易数据。请检查代码或日期范围。"
    except Exception as e:
        return f"下载代码'{symbol}'的历史数据时发生错误: {e}"
    try:
        period_high = hist_df['high'].max()
        period_low = hist_df['low'].min()
        price_difference = period_high - period_low
        result_json = {
            "analysis_type": "stock_price_range",
            "stock_identifier": name or symbol,
            "query_period_start": start_date,
            "query_period_end": end_date,
            "adjust_type": adjust if adjust else "non-adjusted",
            "calculation_result": {
                "period_high": f"{period_high:.2f}",
                "period_low": f"{period_low:.2f}",
                "price_difference": f"{price_difference:.2f}"
            }
        }
        return result_json
    except KeyError as ke:
        return f"错误：返回的数据中缺少必需的列: {ke}。无法进行计算。"
    except Exception as e:
        return f"计算价格差时发生错误: {e}"
