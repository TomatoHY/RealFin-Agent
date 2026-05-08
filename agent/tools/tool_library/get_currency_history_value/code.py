import akshare as ak

from typing import Union

from ..utils import CURRENCY_API_KEY


def get_currency_history_value(
base: str, 
    date: str, 
    currency: str, 
    column_label: str
) -> Union[str, float, int, None]:
    """
    获取指定基准货币在特定历史日期的汇率数据。
    """

    try:
        currency_history_df = ak.currency_history(
            base=base, 
            date=date, 
            symbols="", 
            api_key=CURRENCY_API_KEY
        )
        if currency_history_df.empty:
            return f"错误: API 未能返回 {date} 的任何历史数据。"
        currency_history_df.set_index('currency', inplace=True)
        value_series = currency_history_df.get(column_label)
        if value_series is None:
            raise KeyError(f"列 '{column_label}' 不存在。")
        value = value_series.get(currency)
        if value is None:
            raise KeyError(f"货币 '{currency}' 不存在。")
        final_value = value.item() if hasattr(value, 'item') else value
        result_json = {
            "base_currency": base,
            "target_currency": currency,
            "date": date,
            "metric_name": column_label,
            "value": final_value
        }
        return result_json
    except KeyError as e:
        return f"错误: 在 {date} 的数据中找不到货币或列。详细信息: {e}"
    except Exception as e:
        return f"查询时发生错误: {e}"
