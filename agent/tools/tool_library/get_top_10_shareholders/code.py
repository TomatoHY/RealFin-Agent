import re

import akshare as ak
import pandas as pd

from typing import Optional

from ..utils import _log_debug


def get_top_10_shareholders(
date: str, stock_code: str
) -> Optional[str]:
    symbol = re.sub(r'\D', '', str(stock_code))
    formatted_date = date.replace('-', '')
    if re.match(r'^6', symbol): prefixed_symbol = f"sh{symbol}"
    else: prefixed_symbol = f"sz{symbol}"
    cache_key = (prefixed_symbol, formatted_date)
    try:
        if cache_key not in _top_10_sh_cache:
            _log_debug(f"缓存未命中，为代码'{prefixed_symbol}'在'{formatted_date}'下载十大股东数据...")
            df = ak.stock_gdfx_top_10_em(symbol=prefixed_symbol, date=formatted_date)
            _top_10_sh_cache[cache_key] = df if isinstance(df, pd.DataFrame) else None
            _log_debug("数据缓存成功。")
        df = _top_10_sh_cache[cache_key]
        if df is None: return f"错误: 未能获取数据。可能日期'{date}'无效或非报告期。"
        shareholders_list = []
        target_columns = ['名次', '股东名称', '持股数', '占总股本持股比例', '增减']
        if not all(col in df.columns for col in target_columns):
            return f"错误: 返回的数据缺少必要的列。需要: {target_columns}"
        filtered_df = df[target_columns]
        for index, row in filtered_df.iterrows():
            shareholder_info = {
                "rank": row.get('名次'),
                "name": row.get('股东名称'),
                "shares_held": row.get('持股数'),
                "percentage_of_total_shares": row.get('占总股本持股比例'),
                "change_status": row.get('增减')
            }
            shareholders_list.append(shareholder_info)
        result_json = {
            "stock_identifier": stock_code,
            "report_date": date,
            "data_source": "Top 10 Shareholders (Eastmoney)",
            "shareholders": shareholders_list
        }
        return result_json
    except ValueError as ve:
        if "Length mismatch" in str(ve):
            _top_10_sh_cache[cache_key] = None
            return f"错误: 日期'{date}'很可能不是一个有效的报告期末，导致底层库查询失败。"
        else:
            return f"查询十大股东时发生值错误: {ve}"
    except Exception as e:
        return f"查询十大股东时发生未知错误: {e}"
