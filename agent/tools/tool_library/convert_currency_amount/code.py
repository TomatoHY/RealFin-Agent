import akshare as ak

from datetime import datetime
from typing import Union

from ..utils import CURRENCY_API_KEY


def convert_currency_amount(
base_currency: str,
    target_currency: str,
    amount: float
) -> Union[float, str]:
    """货币金额换算"""
    try:
        amount_str = str(amount)
        convert_df = ak.currency_convert(
            base=base_currency,
            to=target_currency,
            amount=amount_str,
            api_key=CURRENCY_API_KEY
        )
        if convert_df.empty:
            return "错误: API 未能返回换算结果。"
        convert_df.set_index('item', inplace=True)
        converted_value = float(convert_df.loc['value', 'value'])
        exchange_rate = float(convert_df.loc['rate', 'value'])
        last_updated_ts = int(convert_df.loc['updated', 'value'])
        last_updated_time = datetime.fromtimestamp(last_updated_ts).isoformat()
        result_json = {
            "base_currency": base_currency,
            "target_currency": target_currency,
            "original_amount": amount,
            "converted_amount": f"{converted_value:.4f}",
            "exchange_rate": exchange_rate,
            "rate_last_updated": last_updated_time
        }
        return result_json
    except KeyError:
        return f"错误: API 返回的数据格式不正确，无法找到换算结果 'value'。"
    except Exception as e:
        return f"换算时发生错误: {e}"
