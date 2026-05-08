import akshare as ak
import pandas as pd

from datetime import datetime
from typing import Optional

from ..get_code_from_name import get_code_from_name


def calculate_a_stock_change_pct_in_period(
start_date: str,
    end_date: str,
    adjust: str,
    name: Optional[str] = None,
    code: Optional[str] = None
) -> str:
    """
    计算A股某只股票在【指定时间段内】的累计涨跌幅（百分比）。
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
    if start_date_dt >= end_date_dt:
        return f"错误: 开始日期 {start_date} 必须早于结束日期 {end_date}。"
    symbol = code if code else get_code_from_name(name, market='a')
    if not symbol:
        return f"错误：未能通过名称 '{name}' 或代码 '{code}' 找到对应的A股代码。"
    try:
        hist_df = ak.stock_zh_a_hist_tx(
            symbol=symbol,
            adjust=adjust,
            start_date=start_date_ak,
            end_date=end_date_ak
        )
        if hist_df is None or hist_df.empty:
            return f"错误: 在指定时间段内未能获取到代码'{symbol}'的任何交易数据。请检查代码或日期范围。"
        hist_df['date'] = pd.to_datetime(hist_df['date'])
        hist_df.sort_values(by='date', inplace=True)
    except Exception as e:
        return f"下载代码'{symbol}'的历史数据时发生错误: {e}"
    try:
        first_day_data = hist_df.iloc[0]
        last_day_data = hist_df.iloc[-1]
        start_price = first_day_data['close']
        end_price = last_day_data['close']
        actual_start_date = first_day_data['date'].strftime('%Y-%m-%d')
        actual_end_date = last_day_data['date'].strftime('%Y-%m-%d')
        if start_price == 0:
            return f"错误：起始交易日 {actual_start_date} 的收盘价为0，无法计算涨跌幅。"
        change_pct = ((end_price - start_price) / start_price) * 100
        result_json = {
            "stock_name": name,
            "stock_code": symbol,
            "query_period_start": start_date,
            "query_period_end": end_date,
            "actual_trading_day_start": actual_start_date,
            "actual_trading_day_end": actual_end_date,
            "start_price": f"{start_price:.2f}",
            "end_price": f"{end_price:.2f}",
            "change_percentage": f"{change_pct:+.2f}%"
        }
        return result_json
    except (KeyError, IndexError) as e:
        return f"错误：返回的数据格式不正确，无法提取收盘价或首末日期。({e})"
    except Exception as e:
        return f"计算涨跌幅时发生错误: {e}"
