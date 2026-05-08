import akshare as ak
import pandas as pd

from ..utils import _log_debug


def get_stock_sse_deal_daily_value(date: str, row_label: str, column_label: str):
    """
    查询上交所(SSE)在特定交易日的单日成交概况。
    """
    try:
        formatted_date = pd.to_datetime(date).strftime('%Y%m%d')
        stock_sse_deal_daily_df = ak.stock_sse_deal_daily(date=formatted_date)
        if stock_sse_deal_daily_df is None or stock_sse_deal_daily_df.empty:
            _log_debug(f"警告: 日期 {date} 没有返回任何数据，可能是非交易日。")
            return None
        stock_sse_deal_daily_df.set_index('单日情况', inplace=True)
        if row_label not in stock_sse_deal_daily_df.index:
            raise KeyError(f"项目(行) '{row_label}' 不存在。")
        if column_label not in stock_sse_deal_daily_df.columns:
            raise KeyError(f"市场(列) '{column_label}' 不存在。")
        value = stock_sse_deal_daily_df.loc[row_label, column_label]
        result_json = {
            "market": "上海证券交易所(SSE)",
            "data_type": "Daily Deal Summary",
            "date": date,
            "requested_item": {
                "row": row_label,
                "column": column_label,
                "value": value
            }
        }
        return result_json
    except (KeyError, ValueError) as e:
        _log_debug(f"查询失败: {e}")
        if 'stock_sse_deal_daily_df' in locals() and stock_sse_deal_daily_df is not None:
            available_rows = stock_sse_deal_daily_df.index.tolist()
            available_cols = stock_sse_deal_daily_df.columns.tolist()
            _log_debug(f"可用项目(行)包括: {available_rows}")
            _log_debug(f"可用市场(列)包括: {available_cols}")
        return None
    except Exception as e:
        _log_debug(f"获取未知错误: {e}")
        return None
