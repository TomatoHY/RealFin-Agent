import akshare as ak
import pandas as pd

from typing import Union

from ..utils import _log_debug


def get_sw_index_third_info() -> Union[pd.DataFrame, str]:
    """
    获取申万三级行业信息
    
    Returns:
        Union[pd.DataFrame, str]: 
            - 成功: 返回包含申万三级行业信息的DataFrame，包含：
                - 行业代码、行业名称、上级行业、成份个数
                - 静态市盈率、TTM(滚动)市盈率、市净率、静态股息率
            - 失败: 返回错误信息字符串
    """
    _log_debug("--- 正在获取申万三级行业信息... ---")
    try:
        df = ak.sw_index_third_info()
        if df is None or df.empty:
            return "错误: 未能获取申万三级行业信息。"
        _log_debug(f"--- 成功获取 {len(df)} 个申万三级行业 ---")
        return df
    except Exception as e:
        error_msg = f"错误: 获取申万三级行业信息时出错: {str(e)}"
        _log_debug(f"  -> {error_msg}")
        return error_msg
