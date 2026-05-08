import akshare as ak
import pandas as pd

from typing import Union

from ..utils import _log_debug


def get_sw_index_third_cons(
symbol: str
) -> Union[pd.DataFrame, str]:
    """
    获取申万三级行业的成份股数据
    
    Args:
        symbol (str): 行业代码（如"850111.SI"），可以通过 get_sw_index_third_info() 获取
    
    Returns:
        Union[pd.DataFrame, str]: 
            - 成功: 返回包含行业成份股数据的DataFrame，包含：
                - 股票代码、股票简称、纳入时间、申万1/2/3级分类
                - 价格、市盈率、市盈率ttm、市净率、股息率、市值
                - 归母净利润同比增长、营业收入同比增长等
            - 失败: 返回错误信息字符串
    """
    _log_debug(f"--- 正在获取申万三级行业 '{symbol}' 的成份股数据... ---")
    try:
        df = ak.sw_index_third_cons(symbol=symbol)
        if df is None or df.empty:
            return f"错误: 未能获取行业 '{symbol}' 的成份股数据（可能行业代码不正确）。"
        _log_debug(f"--- 成功获取行业 '{symbol}' 的 {len(df)} 只成份股 ---")
        return df
    except Exception as e:
        error_msg = f"错误: 获取行业 '{symbol}' 成份股数据时出错: {str(e)}"
        _log_debug(f"  -> {error_msg}")
        return error_msg
