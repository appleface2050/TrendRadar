"""
美国动态因子模型

提取三个核心因子：
1. 经济增长因子（GDP Growth）
2. 通胀因子（Inflation）
3. 流动性因子（Liquidity）

数据来源：FRED数据库
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.dfm.base_dfm import BaseDFM, SparseDFM
from data.us.us_data_manager import USDataManager


class USDFM(BaseDFM):
    """
    美国动态因子模型

    提取三个核心宏观因子：
    - 经济增长因子：GDP、工业产值、零售销售、非农就业、PMI等
    - 通胀因子：CPI、PCE、PPI、核心通胀等
    - 流动性因子：M1/M2、联邦基金利率、国债收益率、信用利差等
    """

    # 经济增长相关指标
    GROWTH_INDICATORS = [
        'GDP',           # GDP
        'INDPRO',        # 工业产值指数
        'RSXFS',         # 零售销售（不含食品服务）
        'PAYEMS',        # 非农就业人数
        'MANEMP',        # 制造业就业
        'UMCSENT',       # 消费者信心
        'NAPM',          # PMI（制造业指数）
        'CBIC1',         # 哥伦比亚地区PMI
    ]

    # 通胀相关指标
    INFLATION_INDICATORS = [
        'CPIAUCSL',      # CPI（所有城市消费者，所有项目）
        'CPILFESL',      # 核心CPI（不含食品和能源）
        'PCEPI',         # PCE价格指数
        'DFEDTARU',      # 核心PCE
        'PPIACO',        # PPI（所有商品）
        'WPSFD49207',    # PPI（不含食品和能源）
    ]

    # 流动性相关指标
    LIQUIDITY_INDICATORS = [
        'M1SL',          # M1货币存量
        'M2SL',          # M2货币存量
        'BOGMBASE',      # 基础货币
        'FEDFUNDS',      # 联邦基金利率
        'GS10',          # 10年期国债收益率
        'GS2',           # 2年期国债收益率
        'AAA',           # AAA级公司债收益率
        'BAA',           # BAA级公司债收益率
        'DGS10',         # 10年期国债收益率（替代）
        'T10Y2Y',        # 10年-2年期利差
        'TEDRATE',       # TED利差
    ]

    def __init__(
        self,
        n_factors: int = 3,
        factor_orders: int = 2,
        standardize: bool = True,
        data_manager: Optional[USDataManager] = None
    ):
        """
        初始化美国DFM模型

        Parameters
        ----------
        n_factors : int
            因子数量（默认3个：增长、通胀、流动性）
        factor_orders : int
            因子自回归阶数
        standardize : bool
            是否标准化数据
        data_manager : USDataManager, optional
            数据管理器，如果为None则创建新的
        """
        super().__init__(n_factors, factor_orders, standardize)

        self.data_manager = data_manager or USDataManager()

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
        从数据库获取美国宏观数据

        Parameters
        ----------
        start_date : str
            开始日期
        end_date : str, optional
            结束日期，默认为今天
        indicators : list, optional
            指标列表，如果为None则使用所有预定义指标

        Returns
        -------
        pd.DataFrame
            宏观数据（宽表格式，日期为索引，指标为列）
        """
        if indicators is None:
            # 合并所有指标
            indicators = (
                self.GROWTH_INDICATORS +
                self.INFLATION_INDICATORS +
                self.LIQUIDITY_INDICATORS
            )

        # 从数据库获取数据
        # 注意：需要确保数据管理器有相应的方法
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
            raise ValueError("未能获取任何数据，请检查数据库连接和指标代码")

        # 合并所有序列
        combined_data = pd.concat(all_data, axis=1)

        print(f"成功获取 {len(combined_data.columns)} 个指标，{len(combined_data)} 个时间点")
        print(f"数据时间范围：{combined_data.index.min()} 至 {combined_data.index.max()}")
        print(f"缺失率：{combined_data.isnull().sum().sum() / combined_data.size * 100:.2f}%")

        return combined_data

    def fetch_from_csv(
        self,
        csv_path: str = 'data/processed/us/all_indicators.csv',
        start_date: str = '2014-01-01',
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        从CSV文件加载数据（备选方案）

        Parameters
        ----------
        csv_path : str
            CSV文件路径
        start_date : str
            开始日期
        end_date : str, optional
            结束日期

        Returns
        -------
        pd.DataFrame
            宏观数据（宽表格式）
        """
        # 读取CSV
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        df['date'] = pd.to_datetime(df['date'])

        # 过滤日期范围
        df = df[df['date'] >= start_date]
        if end_date:
            df = df[df['date'] <= end_date]

        # 转为宽表格式
        df_wide = df.pivot(
            index='date',
            columns='indicator_code',
            values='value'
        )

        print(f"从CSV加载 {len(df_wide.columns)} 个指标，{len(df_wide)} 个时间点")
        print(f"数据时间范围：{df_wide.index.min()} 至 {df_wide.index.max()}")

        return df_wide

    def calculate_growth_rate(
        self,
        data: pd.DataFrame,
        indicators: Optional[List[str]] = None,
        periods: int = 1
    ) -> pd.DataFrame:
        """
        计算同比增长率（适用于存量指标如GDP、M1/M2）

        Parameters
        ----------
        data : pd.DataFrame
            原始数据
        indicators : list, optional
            需要计算增长率的指标
        periods : int
            滞后期（默认为1，即环比；12为同比）

        Returns
        -------
        pd.DataFrame
            处理后的数据（部分为增长率）
        """
        if indicators is None:
            # 默认对存量指标计算增长率
            indicators = ['GDP', 'M1SL', 'M2SL', 'BOGMBASE']

        data_transformed = data.copy()

        for indicator in indicators:
            if indicator in data_transformed.columns:
                # 计算百分比变化
                data_transformed[f'{indicator}_growth'] = data_transformed[indicator].pct_change(
                    periods=periods
                ) * 100

        return data_transformed

    def fit(
        self,
        data: pd.DataFrame,
        method: str = 'pca',
        transform_to_growth: bool = True
    ) -> 'USDFM':
        """
        拟合美国DFM模型

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

        # 移除无穷值
        data = data.replace([np.inf, -np.inf], np.nan)

        # 对缺失值过多的列进行过滤
        missing_ratio = data.isnull().sum() / len(data)
        valid_cols = missing_ratio[missing_ratio < 0.5].index  # 保留缺失率<50%的列
        data = data[valid_cols]

        # 使用前向填充和后向填充处理缺失值
        data = data.fillna(method='ffill').fillna(method='bfill')

        # 最后删除仍有缺失值的行（应该很少了）
        data = data.dropna()

        print(f"数据预处理：保留 {len(data.columns)} 个指标，{len(data)} 个时间点")

        # 拟合模型
        super().fit(data, method=method)

        return self

    def interpret_factors(
        self,
        data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Dict]:
        """
        解释美国因子的经济含义

        Returns
        -------
        interpretation : dict
            因子解释
        """
        if data is None and hasattr(self, 'data_manager'):
            # 尝试从数据管理器获取数据
            try:
                data = self.fetch_from_csv()
            except:
                pass

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
                # 如果loadings是numpy数组
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
            0: "经济增长因子：反映整体经济活动水平，高值通常对应经济扩张期",
            1: "通胀因子：反映物价水平变化，高值对应高通胀环境",
            2: "流动性因子：反映金融市场流动性状况，受货币政策影响"
        }
        return descriptions.get(factor_index, "未知因子")


def test_us_dfm():
    """
    测试美国DFM模型
    """
    print("=" * 60)
    print("测试美国动态因子模型")
    print("=" * 60)

    # 创建模型
    us_dfm = USDFM(
        n_factors=3,
        factor_orders=2,
        standardize=True
    )

    # 从CSV加载数据
    print("\n[1] 加载数据...")
    data = us_dfm.fetch_from_csv(
        csv_path='data/processed/us/all_indicators.csv',
        start_date='2014-01-01'
    )

    # 拟合模型
    print("\n[2] 拟合DFM模型...")
    us_dfm.fit(data, method='pca')

    # 获取因子
    print("\n[3] 提取因子...")
    factors = us_dfm.get_factors()
    print(f"\n因子统计摘要：")
    print(factors.describe())

    # 解释因子
    print("\n[4] 解释因子经济含义...")
    interpretation = us_dfm.interpret_factors(data)
    for factor_name, info in interpretation.items():
        print(f"\n{factor_name}: {info['economic_meaning']}")
        print(f"描述：{info['description']}")
        print(f"主要驱动指标：{info['top_indicators'][:5]}")

    # 绘制因子
    print("\n[5] 绘制因子时序图...")
    fig = us_dfm.plot_factors(figsize=(12, 8))
    fig.savefig('models/dfm/us_factors_plot.png', dpi=100, bbox_inches='tight')
    print("图表已保存到：models/dfm/us_factors_plot.png")

    # 因子稳定性检验
    print("\n[6] 检验因子稳定性...")
    stability = us_dfm.get_factor_stability(window=126)  # 约6个月
    print(f"因子间滚动相关系数（最后时期）：")
    print(stability.iloc[-1])

    return us_dfm, factors


if __name__ == '__main__':
    # 运行测试
    us_dfm, factors = test_us_dfm()
