from typing import Optional
import akshare as ak

from datetime import datetime

from ..utils import CURRENCY_API_KEY


def get_current_latest_value(
    base: str,
    currency: str,
    column_label: str,
    symbol: Optional[str] = None
):
    """
    获取指定基准货币的最新汇率数据。
    """
    try:
        currency_latest_df = ak.currency_latest(
            base=base,
            symbols=symbol,
            api_key=CURRENCY_API_KEY
        )
        if currency_latest_df is None or currency_latest_df.empty:
            return {"error": "API 未能返回任何最新的汇率数据。"}

        # API 返回的列名是 'rates'，但用户可能传入 'value'
        # 创建列名映射
        column_mapping = {
            'value': 'rates',
            'rate': 'rates',
            'rates': 'rates'
        }

        # 映射列名
        actual_column = column_mapping.get(column_label.lower(), column_label)

        currency_latest_df.set_index('currency', inplace=True)
        if currency not in currency_latest_df.index:
            return {"error": f"货币 '{currency}' 不在返回的数据中。"}
        if actual_column not in currency_latest_df.columns:
            return {"error": f"列 '{column_label}' (映射为 '{actual_column}') 不在返回的数据中。可用列: {list(currency_latest_df.columns)}"}

        value = currency_latest_df.loc[currency, actual_column]
        final_value = value.item() if hasattr(value, 'item') else value
        row_data = currency_latest_df.loc[currency]

        # 从 date 列提取时间戳作为 last_updated
        try:
            if 'date' in row_data.index:
                date_val = row_data['date']
                if hasattr(date_val, 'isoformat'):
                    last_updated_time = date_val.isoformat()
                else:
                    last_updated_time = str(date_val)
            else:
                last_updated_time = "N/A"
        except Exception:
            last_updated_time = "N/A"

        result_json = {
            "base_currency": base,
            "target_currency": currency,
            "data_type": "latest_realtime",
            "metric_name": column_label,
            "value": final_value,
            "rate_last_updated": last_updated_time
        }
        return result_json
    except KeyError as e:
        return {"error": f"查询失败: {str(e)}"}
    except Exception as e:
        return {"error": f"查询时发生未知错误: {str(e)}"}
