import akshare as ak
import pandas as pd

from typing import Optional


def get_nbs_region_data(
kind: str,
    path: str,
    period: str,
    region: Optional[str] = None,
    indicator: Optional[str] = None,
    target_label: Optional[str] = None,
    target_time: Optional[str] = None
) -> str:
    """获取国家统计局地区数据"""
    if not indicator and not region:
        return "错误：参数 'indicator' (指标) 和 'region' (地区) 不能同时为空。"
    try:
        df: pd.DataFrame = ak.macro_china_nbs_region(
            kind=kind, path=path, period=period, indicator=indicator, region=region
        )
        if df.empty:
            return "查询成功，但未返回任何数据。请检查参数是否正确或该条件下是否有数据。"
        if target_label and target_time:
            try:
                clean_label = target_label.strip()
                clean_time = target_time.strip()
                value = df.loc[clean_label, clean_time]
                final_value = value.item() if hasattr(value, 'item') else value
                result_json = {
                    "source": "国家统计局(NBS)",
                    "kind": kind,
                    "path": path,
                    "query_params": {
                        "region": region,
                        "indicator": indicator,
                        "period": period
                    },
                    "result": {
                        "row_label": clean_label,
                        "column_label_time": clean_time,
                        "value": final_value
                    }
                }
                return result_json
            except KeyError:
                available_rows = df.index.to_list()
                available_cols = df.columns.to_list()
                return (
                    f"错误：找不到指定的行标签 '{target_label}' 或列标签 '{target_time}'。\n"
                    f"可用的行标签: {available_rows}\n"
                    f"可用的列标签: {available_cols}"
                )
        else:
            summary_json = {
                "summary": "数据查询成功，已获取到数据概览。",
                "guidance": "请提供 'target_label' (行标签) 和 'target_time' (列标签/时间) 以获取具体数值。",
                "data_preview": {
                    "available_row_labels_sample": available_rows[:10], 
                    "available_column_labels_sample": available_cols[:10] 
                }
            }
            return summary_json
    except Exception as e:
        return f"查询数据时发生错误: {e}。请检查您的参数是否与官网完全匹配。"
