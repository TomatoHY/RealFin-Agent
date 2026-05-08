import akshare as ak
import pandas as pd

from typing import Union

from ..utils import _log_debug


def get_stock_board_industry_list() -> Union[pd.DataFrame, str]:
    """
    获取东方财富-行业板块的所有板块列表
    
    Returns:
        Union[pd.DataFrame, str]: 
            - 成功: 返回包含板块代码和名称的DataFrame
            - 失败: 返回错误信息字符串
    """
    _log_debug("--- 正在获取东方财富行业板块列表... ---")
    try:
        df = ak.stock_board_industry_name_em()
        if df is None or df.empty:
            return "错误: 未能获取板块列表数据。"
        _log_debug(f"--- 成功获取 {len(df)} 个行业板块 ---")
        return df
    except Exception as e:
        error_msg = f"错误: 获取行业板块列表时出错: {str(e)}"
        _log_debug(f"  -> {error_msg}")
        return error_msg
