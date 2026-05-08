import re

import akshare as ak
import pandas as pd

from typing import Optional, Any

from ..get_code_from_name.code import get_code_from_name
from ..utils import _log_debug, _dividend_allotment_cache


def get_dividend_allotment_history(
report_period: str,
    column_label: str,
    name: Optional[str] = None,
    code: Optional[str] = None
) -> Optional[Any]:
    """
    查询A股公司历史分红配送数据。
    """
    global _dividend_allotment_cache
    symbol_from_input = code if code else get_code_from_name(name)
    if not symbol_from_input: 
        return f"错误: 无法找到代码 for '{name or code}'."
    symbol = re.sub(r'\D', '', str(symbol_from_input))
    try:
        if symbol not in _dividend_allotment_cache:
            _log_debug(f"缓存未命中，为代码'{symbol}'下载历史分红配送数据...")
            df = ak.stock_fhps_detail_em(symbol=symbol)
            if isinstance(df, pd.DataFrame) and not df.empty:
                df['报告期'] = pd.to_datetime(df['报告期']).dt.strftime('%Y-%m-%d')
                _dividend_allotment_cache[symbol] = df
            else:
                _dividend_allotment_cache[symbol] = None
            _log_debug("数据缓存成功。")
        df = _dividend_allotment_cache[symbol]
        if df is None:
            return f"错误: 未能获取代码'{symbol}'的分红配送数据。"
        df_indexed = df.set_index('报告期')
        if column_label not in df_indexed.columns:
            raise KeyError(f"指标 '{column_label}' 无效。")
        if report_period not in df_indexed.index:
            raise KeyError(f"报告期 '{report_period}' 不存在。")
        value = df_indexed.loc[report_period, column_label]
        plan_description = df_indexed.loc[report_period, '分红方案说明'] 
        result_json = {
            "stock_identifier": name or symbol_from_input,
            "report_period": report_period,
            "metric_name": column_label,
            "value": value,
            "dividend_plan_description": plan_description
        }
        return result_json
    except KeyError as e:
        if 'df' in locals() and df is not None:
            available_periods = df['报告期'].unique().tolist()
            available_columns = df.columns.tolist()
            return (f"查询失败: {e}\n"
                    f"请检查您的输入。\n"
                    f"可用报告期示例: {available_periods[:5]}...\n"
                    f"可用指标: {available_columns}")
        return f"查询失败: {e}"
    except Exception as e:
        return f"查询分红配送时出错: {e}"
