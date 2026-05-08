import akshare as ak
import pandas as pd

from typing import Union

from ..utils import _log_debug


def get_stock_board_industry_cons(
symbol: str
) -> Union[pd.DataFrame, str]:
    """
    获取东方财富-行业板块的成份股数据
    
    Args:
        symbol (str): 板块名称（如"小金属"）或板块代码（如"BK1027"）
    
    Returns:
        Union[pd.DataFrame, str]: 
            - 成功: 返回包含板块成份股数据的DataFrame，包含：
                - 代码、名称、最新价、涨跌幅、涨跌额、成交量、成交额
                - 振幅、最高、最低、今开、昨收、换手率、市盈率-动态、市净率
            - 失败: 返回错误信息字符串
    """
    _log_debug(f"--- 正在获取板块 '{symbol}' 的成份股数据... ---")
    try:
        df = ak.stock_board_industry_cons_em(symbol=symbol)
        if df is None or df.empty:
            return f"错误: 未能获取板块 '{symbol}' 的成份股数据（可能板块名称或代码不正确）。"
        
        # 确保列名标准化
        if '代码' in df.columns:
            df = df.rename(columns={'代码': 'code', '名称': 'name'})
        
        _log_debug(f"--- 成功获取板块 '{symbol}' 的 {len(df)} 只成份股 ---")
        return df
    except Exception as e:
        error_msg = f"错误: 获取板块 '{symbol}' 成份股数据时出错: {str(e)}"
        _log_debug(f"  -> {error_msg}")
        return error_msg
