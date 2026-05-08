import re

import akshare as ak
import pandas as pd

from typing import Optional, Any

from ..utils import _log_debug


def get_stock_basic_info(
    symbol: str, 
    item_name: str, 
    report_date: Optional[str] = None, 
    us_report_type: str = "年报"
) -> Optional[Any]:
    """
    获取股票信息。
    - A股: 从东方财富获取基础信息。
    - 美股: 使用 AkShare 的【财务报表接口】获取详细行项目。
    
    :param symbol: 股票代码 (A股或美股)。
    :param item_name: 要查询的信息项。A股字段名为中文（如'公司名称'）；美股字段名为【报表项目中文名】（如'递延所得税资产'）。
    :param report_date: 指定报告日期 (可选)。
    :param us_report_type: 美股报告类型，可选 {"年报", "单季报", "累计季报"}，默认为 "年报"。
    :return: 查询到的指标值。
    """
    _log_debug(f"--- 正在为 '{symbol}' 查询基础信息: '{item_name}' ---")
    try:
        if re.match(r'^(SH|SZ|BJ)\d{6}$', symbol.upper()):
            market_code = symbol[2:]
            _log_debug(f"  -> 检测到 A 股代码，使用东方财富接口查询 '{market_code}'...")
            info_df = ak.stock_individual_info_em(symbol=market_code)
            if info_df is None or info_df.empty:
                return f"错误：未能获取到A股 '{symbol}' 的信息。"
            info_df.set_index("item", inplace=True)
            value = info_df.loc[item_name, 'value']
            result_json = {
                "stock_code": symbol,
                "stock_name": info_df.loc['公司名称', 'value'],
                "market": "A-Share",
                "data_source": "Basic Info",
                "requested_item": {
                    "name": item_name,
                    "value": value
                }
            }
            return result_json
        else:
            if us_report_type not in ["年报", "单季报", "累计季报"]:
                raise ValueError("美股报告类型 us_report_type 必须是 '年报', '单季报' 或 '累计季报' 之一。")
            report_name = "资产负债表" 
            _log_debug(f"  -> 按美股代码处理，使用【AkShare 财务报表接口】查询 '{report_name}' - '{us_report_type}' 的 '{item_name}'...")
            financial_report_df = ak.stock_financial_us_report_em(
                stock=symbol,
                symbol=report_name,
                indicator=us_report_type
            )
            if financial_report_df.empty:
                return f"错误：未能通过 AkShare 获取到 '{symbol}' 的 {report_name} 数据。"
            financial_report_df['REPORT_DATE'] = pd.to_datetime(financial_report_df['REPORT_DATE'])
            financial_report_df.sort_values(by='REPORT_DATE', ascending=False, inplace=True)
            filtered_df = financial_report_df[financial_report_df['ITEM_NAME'] == item_name].copy()
            if filtered_df.empty:
                available_items = financial_report_df['ITEM_NAME'].unique().tolist()
                _log_debug(f"错误：指标 '{item_name}' 不存在于当前报表 ({report_name}) 中。")
                _log_debug(f"当前报表可用项目（部分）：{available_items[:10]}")
                return None
            value = None
            actual_report_date = None
            if report_date:
                target_date = pd.to_datetime(report_date)
                filtered_df['date_diff'] = abs(filtered_df['REPORT_DATE'] - target_date)
                closest_report = filtered_df.loc[filtered_df['date_diff'].idxmin()]
                value = closest_report['AMOUNT']
                actual_report_date = closest_report['REPORT_DATE'].strftime('%Y-%m-%d')
            else:
                latest_report = filtered_df.iloc[0]
                value = latest_report['AMOUNT']
                actual_report_date = latest_report['REPORT_DATE'].strftime('%Y-%m-%d')
        if pd.notna(value):
            result_json = {
                    "stock_code": symbol,
                    "market": "US-Stock",
                    "data_source": f"Financial Report - {report_name} ({us_report_type})",
                    "report_date": actual_report_date,
                    "requested_item": {
                        "name": item_name,
                        "value": float(value),
                        "unit": "USD" 
                    }
                }
            return result_json
        else:
            _log_debug(f"*** 查询成功: '{item_name}' 的值是 -> 无数据 (NaN) ***")
            return None
    except Exception as e:
        _log_debug(f"获取或处理 \'{symbol}' 数据时发生严重错误: {e}")
        return None
