import re

import akshare as ak
import pandas as pd

from typing import Optional, Any

from ..get_code_from_name.code import get_code_from_name
from ..utils import _log_debug, _earnings_announcement_cache


def get_earnings_announcement(
report_date: str,
    item_name: str,
    name: Optional[str] = None,
    code: Optional[str] = None,
) -> Any:
    """
    查询A股公司在特定报告期发布的【业绩预告】。
    """
    global _earnings_announcement_cache
    if not code and not name: return "错误: 必须提供股票代码或名称。"
    symbol_from_input = code if code else get_code_from_name(name)
    if not symbol_from_input: return f"错误: 无法找到代码 for '{name or code}'."
    symbol_code = re.sub(r'\D', '', str(symbol_from_input))
    try:
        formatted_date = pd.to_datetime(report_date).strftime('%Y%m%d')
        if formatted_date not in _earnings_announcement_cache:
            _log_debug(f"缓存未命中，下载'{formatted_date}'的所有业绩预告...")
            df = ak.stock_yjyg_em(date=formatted_date)
            _earnings_announcement_cache[formatted_date] = df if isinstance(df, pd.DataFrame) else None
            _log_debug("数据缓存成功。")
        df = _earnings_announcement_cache[formatted_date]
        if df is None: return f"错误: 未能获取'{formatted_date}'的业绩预告数据。"
        stock_df = df[df['股票代码'] == symbol_code].copy()
        if stock_df.empty: return f"查询失败: 未找到代码'{symbol_code}'在'{report_date}'的业绩预告。"
        stock_df['公告日期'] = pd.to_datetime(stock_df['公告日期'])
        latest_announcement = stock_df.sort_values(by='公告日期', ascending=False).iloc[0]
        if item_name not in latest_announcement.index:
            raise KeyError
        value = latest_announcement[item_name]
        stock_name_from_data = latest_announcement.get('股票简称', name)
        announcement_date = latest_announcement['公告日期'].strftime('%Y-%m-%d')
        forecast_type = latest_announcement.get('预告类型', 'N/A')
        result_json = {
            "stock_code": symbol_code,
            "stock_name": stock_name_from_data,
            "report_date": report_date,
            "announcement_date": announcement_date, 
            "forecast_type": forecast_type,
            "requested_item": item_name,
            "value": value
        }
        return result_json 
    except KeyError:
        if 'latest_announcement' in locals():
            available_items = latest_announcement.index.tolist()
            return f"查询失败: 预告中不存在'{item_name}'字段。可用字段: {available_items}"
        return f"查询失败: 预告中不存在'{item_name}'字段。"
    except Exception as e:
        return f"查询业绩预告时出错: {e}"
