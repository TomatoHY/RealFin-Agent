import akshare as ak
import pandas as pd

from typing import Literal

from ..utils import _log_debug, _population_cache


def get_china_population_nbs(
population_metric: Literal["total", "male", "female", "urban", "rural"],
    query_year: str = "latest"
) -> dict:
    """
    从国家统计局(NBS)查询中国的年度人口数据 (已修复value为整数类型)。
    """
    global _population_cache
    METRIC_TO_ROW_MAP = {
        "total": "年末总人口(万人)",
        "male": "男性人口(万人)",
        "female": "女性人口(万人)",
        "urban": "城镇人口(万人)",
        "rural": "乡村人口(万人)"
    }
    target_row_name = METRIC_TO_ROW_MAP.get(population_metric)
    if not target_row_name:
        return {"error": f"无效的人口指标 '{population_metric}'。"}
    try:
        if _population_cache is None:
            _log_debug(f"--- [API 调用] 缓存未命中，正在通过 akshare 下载中国年度人口数据... ---")
            df = ak.macro_china_nbs_nation(kind="年度数据", path="人口 > 总人口", period="2000-")
            if df.empty:
                return {"error": "从国家统计局接口获取人口数据失败，返回为空。"}
            _population_cache = df
        df = _population_cache
        _log_debug(f"--- [函数缓存] 成功从缓存中读取人口数据。 ---")
    except Exception as e:
        return {"error": f"调用 akshare 接口或处理数据时失败: {e}"}
    try:
        target_column_name = ""
        if query_year.lower() == "latest":
            target_column_name = df.columns[0]
        else:
            target_column_name = f"{query_year}年"
        if target_column_name not in df.columns:
            available_years = [col.replace('年', '') for col in df.columns]
            return {"error": f"未能找到年份 '{query_year}' 的数据。可用年份示例: {available_years[:5]}..."}
        value = df.loc[target_row_name, target_column_name]
        if pd.isna(value):
            return {"error": f"在 {target_column_name} 找到了指标 '{target_row_name}'，但其数值为空。"}
        year_str = target_column_name.replace('年', '')
        result_json = {
            "source": "国家统计局(NBS)",
            "region": "中国",
            "year": int(year_str),
            "metric_name": target_row_name.split('(')[0],
            "value": int(value), 
            "unit": "万人"
        }
        return result_json
    except KeyError as e:
        return {"error": f"查询数据时发生键错误，可能是指标 '{target_row_name}' 不存在: {e}"}
    except Exception as e:
        return {"error": f"查询时发生未知错误: {e}"}
