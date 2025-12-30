"""
中国动态因子模型

提取三个核心因子：
1. 经济增长因子（GDP Growth）
2. 通胀因子（Inflation）
3. 流动性因子（Liquidity）

数据来源：Tushare、Akshare
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.dfm.base_dfm import BaseDFM, SparseDFM
from data_handlers.cn.cn_data_manager import CNDataManager


class CNDFM(BaseDFM):
    """
    中国动态因子模型

    提取三个核心宏观因子：
    - 经济增长因子：GDP、工业增加值、社零、固定资产投资、PMI等
    - 通胀因子：CPI、PPI、核心CPI等
    - 流动性因子：M1/M2、社融、SHIBOR、DR007等
    """

    # 经济增长相关指标
    GROWTH_INDICATORS = [
        'GDP',           # GDP
        'IND_PROD',      # 工业增加值
        'RETAIL_SALES',  # 社会消费品零售总额
        'FAI',           # 固定资产投资
        'PMI',           # 制造业PMI
        'NONPMI',        # 非制造业PMI
        'EXPORT',        # 出口
        'IMPORT',        # 进口
    ]

    # 通胀相关指标
    INFLATION_INDICATORS = [
        'CPI',           # CPI
        'CORE_CPI',      # 核心CPI
        'PPI',           # PPI
        'PPI_RM',        # PPI（购进价格）
    ]

    # 流动性相关指标
    LIQUIDITY_INDICATORS = [
        'M0',            # M0
        'M1',            # M1
        'M2',            # M2
        'OUTLAY_SH',     # 社会融资规模
        'SHIBOR_O_N',    # SHIBOR隔夜
        'SHIBOR_1W',     # SHIBOR 1周
        'DR007',         # DR007
        'R007',          # R007
        'LOAN_RATE',     # LPR贷款利率
        'MLF_RATE',      # MLF利率
    ]

    def __init__(
        self,
        n_factors: int = 3,
        factor_orders: int = 2,
        standardize: bool = True,
        data_manager: Optional[CNDataManager] = None
    ):
        """
        初始化中国DFM模型

        Parameters
        ----------
        n_factors : int
            因子数量（默认3个：增长、通胀、流动性）
        factor_orders : int
            因子自回归阶数
        standardize : bool
            是否标准化数据
        data_manager : CNDataManager, optional
            数据管理器
        """
        super().__init__(n_factors, factor_orders, standardize)

        self.data_manager = data_manager or CNDataManager()

        # 因子名称映射
        self.factor_names = {
            0: '经济增长因子',
            1: '通胀因子',
            2: '流动性因子'
        }

    def fetch_macro_data(
        self,
        start_date: str = '2010-01-01',
        end_date: Optional[str] = None,
        indicators: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        从数据库获取中国宏观数据

        Parameters
        ----------
        start_date : str
            开始日期
        end_date : str, optional
            结束日期
        indicators : list, optional
            指标列表

        Returns
        -------
        pd.DataFrame
            宏观数据（宽表格式）
        """
        if indicators is None:
            indicators = (
                self.GROWTH_INDICATORS +
                self.INFLATION_INDICATORS +
                self.LIQUIDITY_INDICATORS
            )

        all_data = []

        for indicator in indicators:
            try:
                df = self.data_manager.get_indicator_data(
                    indicator_code=indicator,
                    start_date=start_date,
                    end_date=end_date
                )
                if not df.empty:
                    df_series = df[['date', 'value']].set_index('date')['value']
                    df_series.name = indicator
                    all_data.append(df_series)
            except Exception as e:
                print(f"警告：无法获取 {indicator} 数据：{e}")
                continue

        if not all_data:
            raise ValueError("未能获取任何数据")

        combined_data = pd.concat(all_data, axis=1)

        print(f"成功获取 {len(combined_data.columns)} 个指标，{len(combined_data)} 个时间点")
        print(f"数据时间范围：{combined_data.index.min()} 至 {combined_data.index.max()}")
        print(f"缺失率：{combined_data.isnull().sum().sum() / combined_data.size * 100:.2f}%")

        return combined_data

    def calculate_growth_rate(
        self,
        data: pd.DataFrame,
        indicators: Optional[List[str]] = None,
        periods: int = 1
    ) -> pd.DataFrame:
        """
        计算同比增长率

        Parameters
        ----------
        data : pd.DataFrame
            原始数据
        indicators : list, optional
            需要计算增长率的指标
        periods : int
            滞后期

        Returns
        -------
        pd.DataFrame
            处理后的数据
        """
        if indicators is None:
            indicators = ['GDP', 'M0', 'M1', 'M2', 'OUTLAY_SH']

        data_transformed = data.copy()

        for indicator in indicators:
            if indicator in data_transformed.columns:
                data_transformed[f'{indicator}_growth'] = data_transformed[indicator].pct_change(
                    periods=periods
                ) * 100

        return data_transformed

    def fit(
        self,
        data: pd.DataFrame,
        method: str = 'pca',
        transform_to_growth: bool = True
    ) -> 'CNDFM':
        """
        拟合中国DFM模型

        Parameters
        ----------
        data : pd.DataFrame
            宏观数据
        method : str
            估计方法
        transform_to_growth : bool
            是否将存量指标转换为增长率

        Returns
        -------
        self
        """
        # 数据预处理
        if transform_to_growth:
            data = self.calculate_growth_rate(data)

        # 移除无穷值和NaN
        data = data.replace([np.inf, -np.inf], np.nan)
        data = data.dropna()

        # 拟合模型
        super().fit(data, method=method)

        return self

    def interpret_factors(
        self,
        data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Dict]:
        """
        解释中国因子的经济含义

        Returns
        -------
        interpretation : dict
            因子解释
        """
        # 获取因子载荷
        loadings = self.get_factor_loadings()

        interpretation = {}

        for i in range(self.n_factors):
            factor_key = f'Factor_{i+1}'

            # 找出载荷最大的变量
            if isinstance(loadings, pd.DataFrame):
                top_loadings = loadings[factor_key].abs().sort_values(ascending=False).head(10)
                top_variables = top_loadings.index.tolist()
                loadings_values = top_loadings.values.tolist()
            else:
                loadings_array = np.abs(loadings).flatten()
                top_indices = np.argsort(loadings_array)[-10:][::-1]
                loadings_values = loadings_array[top_indices].tolist()
                top_variables = [f'Var_{i}' for i in top_indices]

            interpretation[factor_key] = {
                'economic_meaning': self.factor_names.get(i, f'因子{i+1}'),
                'top_indicators': top_variables,
                'loadings': loadings_values,
                'description': self._get_factor_description(i)
            }

        return interpretation

    def _get_factor_description(self, factor_index: int) -> str:
        """
        获取因子描述
        """
        descriptions = {
            0: "经济增长因子：反映中国经济活动水平，高值通常对应经济扩张期",
            1: "通胀因子：反映中国物价水平变化，受猪周期、货币政策等影响",
            2: "流动性因子：反映中国金融市场流动性状况，受央行政策影响显著"
        }
        return descriptions.get(factor_index, "未知因子")


def test_cn_dfm():
    """
    测试中国DFM模型
    """
    print("=" * 60)
    print("测试中国动态因子模型")
    print("=" * 60)

    # 创建模型
    cn_dfm = CNDFM(
        n_factors=3,
        factor_orders=2,
        standardize=True
    )

    # 注意：需要先从Tushare获取数据
    # 这里仅展示代码框架，实际运行需要有效数据

    print("\n提示：中国DFM模型已创建")
    print("使用前请确保：")
    print("1. 已配置Tushare Token（confidential.json）")
    print("2. 已获取中国宏观数据并存储到数据库")
    print("3. 运行 cn_dfm.fetch_macro_data() 获取数据")

    return cn_dfm


if __name__ == '__main__':
    # 运行测试
    cn_dfm = test_cn_dfm()
