import akshare as ak

from typing import Optional, Any

from ..get_code_from_name import get_code_from_name
from ..utils import _log_debug, _stock_comment_cache


def get_stock_comment(
    column_label: str,
    name: Optional[str] = None,
    code: Optional[str] = None
) -> Optional[Any]:
    global _stock_comment_cache
    symbol = code if code else get_code_from_name(name)
    if not symbol: return f"错误: 无法找到代码 for '{name or code}'."
    try:
        if _stock_comment_cache is None:
            _log_debug("首次查询，正在下载所有股票的'千股千评'数据...")
            df = ak.stock_comment_em()
            if df.empty: return "错误: 未能获取'千股千评'数据。"
            _stock_comment_cache = df
            _log_debug("数据缓存成功。")
        df = _stock_comment_cache
        stock_row = df[df['代码'] == symbol]
        if stock_row.empty:
            return f"查询失败: 在'千股千评'数据中未找到股票代码'{symbol}'。"
        value = float(stock_row.iloc[0][column_label])
        stock_name_from_data = stock_row.iloc[0].get("名称", name)
        result_json = {
            "stock_code": symbol,
            "stock_name": stock_name_from_data,
            "data_source": "千股千评 (Eastmoney)",
            "requested_item": {
                "name": column_label,
                "value": value
            }
        }
        return result_json
    except Exception as e:
        return f"查询'千股千评'时出错: {e}"
