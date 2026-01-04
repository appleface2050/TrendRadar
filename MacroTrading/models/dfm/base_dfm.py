"""
动态因子模型（Dynamic Factor Model, DFM）基础实现

理论基础：
1. 多个宏观经济序列由少数几个共同因子驱动
2. 因子不可直接观测，需通过状态空间模型估计
3. 支持不同频率的数据（混频数据）

参考文献：
- Stock, J. H., & Watson, M. W. (2002). Macroeconomic forecasting using diffusion indexes.
- Doz, C., Giannone, D., & Reichlin, L. (2011). A quasi-maximum likelihood approach for large, approximate dynamic factor models.
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.dynamic_factor import DynamicFactor
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Optional, Union
import warnings

warnings.filterwarnings('ignore')


class BaseDFM:
    """
    动态因子模型基类

    核心思想：
    X_t = Λ * F_t + e_t  （观测方程）
    F_t = Φ * F_{t-1} + u_t  （转移方程）

    其中：
    - X_t: 可观测的宏观经济变量向量
    - F_t: 不可观测的因子向量（经济增长、通胀、流动性等）
    - Λ: 因子载荷矩阵
    - Φ: 因子自回归系数矩阵
    - e_t, u_t: 误差项
    """

    def __init__(
        self,
        n_factors: int = 3,
        factor_orders: int = 2,
        standardize: bool = True,
    ):
        """
        初始化DFM模型

        Parameters
        ----------
        n_factors : int
            因子数量，默认为3（经济增长、通胀、流动性）
        factor_orders : int
            因子自回归阶数，默认为2
        standardize : bool
            是否标准化数据
        """
        self.n_factors = n_factors
        self.factor_orders = factor_orders
        self.standardize = standardize

        self.model = None
        self.results = None
        self.scaler = StandardScaler() if standardize else None
        self.factors = None
        self.feature_names = None  # 保存原始特征名称

    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        准备数据：处理缺失值、频率对齐、标准化

        Parameters
        ----------
        data : pd.DataFrame
            原始数据，索引为日期，列为各指标

        Returns
        -------
        pd.DataFrame
            处理后的数据
        """
        # 复制数据
        df = data.copy()

        # 检查是否需要处理缺失值
        if df.isnull().any().any():
            print(f"警告：数据存在缺失值，缺失率：{df.isnull().sum().sum() / df.size * 100:.2f}%")
            # 对于少量缺失值，使用前向填充
            df = df.fillna(method='ffill').fillna(method='bfill')

        # 标准化
        if self.standardize:
            df_scaled = pd.DataFrame(
                self.scaler.fit_transform(df),
                index=df.index,
                columns=df.columns
            )
            return df_scaled
        return df

    def fit_pca(
        self,
        data: pd.DataFrame,
        n_factors: Optional[int] = None
    ) -> Tuple[pd.DataFrame, PCA]:
        """
        使用PCA提取初始因子（两步估计法的第一步）

        Parameters
        ----------
        data : pd.DataFrame
            标准化后的数据
        n_factors : int, optional
            因子数量，默认使用self.n_factors

        Returns
        -------
        factors : pd.DataFrame
            估计的因子
        pca : PCA
            PCA对象
        """
        if n_factors is None:
            n_factors = self.n_factors

        pca = PCA(n_components=n_factors)
        factors = pca.fit_transform(data)

        # 转为DataFrame
        factor_names = [f'Factor_{i+1}' for i in range(n_factors)]
        factors_df = pd.DataFrame(
            factors,
            index=data.index,
            columns=factor_names
        )

        print(f"PCA解释方差比：{pca.explained_variance_ratio_}")
        print(f"累计解释方差比：{pca.explained_variance_ratio_.cumsum()}")

        return factors_df, pca

    def fit_state_space(
        self,
        data: pd.DataFrame,
        endog_names: Optional[List[str]] = None
    ):
        """
        使用状态空间模型估计DFM（两步估计法的第二步）

        Parameters
        ----------
        data : pd.DataFrame
            标准化后的数据
        endog_names : list, optional
            因变量名称列表

        Returns
        -------
        results : statsmodels结果对象
        """
        if endog_names is None:
            endog_names = data.columns.tolist()

        # 创建动态因子模型
        # 注意：statsmodels的DynamicFactorMQ更适用于大规模数据
        # 这里使用DynamicFactor作为示例
        try:
            model = DynamicFactor(
                endog=data.values,
                k_factors=self.n_factors,
                factor_orders=self.factor_orders
            )

            # 估计模型
            results = model.fit(disp=False, maxiter=100)

            self.model = model
            self.results = results

            return results

        except Exception as e:
            print(f"状态空间模型估计失败：{e}")
            print("降级为PCA方法...")
            return None

    def fit(self, data: pd.DataFrame, method: str = 'pca') -> 'BaseDFM':
        """
        拟合DFM模型

        Parameters
        ----------
        data : pd.DataFrame
            原始数据
        method : str
            估计方法，'pca' 或 'state_space'

        Returns
        -------
        self
        """
        # 准备数据
        data_prep = self.prepare_data(data)

        # 保存实际使用的特征名称（可能在预处理中被过滤）
        self.feature_names = data_prep.columns.tolist()

        if method == 'pca':
            # PCA方法（快速但精度较低）
            self.factors, self.pca_model = self.fit_pca(data_prep)
        elif method == 'state_space':
            # 状态空间方法（精确但较慢）
            results = self.fit_state_space(data_prep)
            if results is not None:
                # 提取平滑后的因子
                self.factors = pd.DataFrame(
                    results.smoothed_state[:self.n_factors].T,
                    index=data_prep.index,
                    columns=[f'Factor_{i+1}' for i in range(self.n_factors)]
                )
            else:
                # 降级到PCA
                self.factors, self.pca_model = self.fit_pca(data_prep)
        else:
            raise ValueError(f"未知的估计方法：{method}")

        return self

    def get_factors(self) -> pd.DataFrame:
        """
        获取估计的因子

        Returns
        -------
        pd.DataFrame
            因子序列
        """
        if self.factors is None:
            raise ValueError("模型尚未拟合，请先调用fit()方法")
        return self.factors

    def get_factor_loadings(self) -> pd.DataFrame:
        """
        获取因子载荷

        Returns
        -------
        pd.DataFrame
            因子载荷矩阵（变量 x 因子）
        """
        if self.results is not None:
            # 从状态空间模型提取载荷
            loadings = self.results.params['design']
            return pd.DataFrame(loadings)
        elif hasattr(self, 'pca_model'):
            # 从PCA提取载荷
            loadings = pd.DataFrame(
                self.pca_model.components_.T,
                columns=[f'Factor_{i+1}' for i in range(self.n_factors)]
            )

            # 使用原始特征名称作为索引
            if self.feature_names is not None and len(loadings) == len(self.feature_names):
                loadings.index = self.feature_names

            return loadings
        else:
            raise ValueError("无法提取因子载荷")

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        将新数据转换为因子

        Parameters
        ----------
        data : pd.DataFrame
            新数据

        Returns
        -------
        pd.DataFrame
            转换后的因子
        """
        if not hasattr(self, 'pca_model'):
            raise ValueError("模型尚未拟合")

        data_prep = self.prepare_data(data)
        factors = self.pca_model.transform(data_prep)

        return pd.DataFrame(
            factors,
            index=data_prep.index,
            columns=[f'Factor_{i+1}' for i in range(self.n_factors)]
        )

    def interpret_factors(
        self,
        data: pd.DataFrame,
        factor_names: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[str]]:
        """
        解释因子的经济含义（基于载荷）

        Parameters
        ----------
        data : pd.DataFrame
            原始数据（用于获取变量名）
        factor_names : dict, optional
            因子名称映射，如 {0: '经济增长', 1: '通胀', 2: '流动性'}

        Returns
        -------
        interpretation : dict
            因子经济含义解释
        """
        loadings = self.get_factor_loadings()
        interpretation = {}

        for i in range(self.n_factors):
            factor_key = f'Factor_{i+1}'

            # 找出载荷最大的5个变量
            top_loadings = loadings[factor_key].abs().sort_values(ascending=False).head(5)
            top_variables = top_loadings.index.tolist()

            interpretation[factor_key] = {
                'top_variables': top_variables,
                'loadings': top_loadings.values.tolist(),
                'interpretation': factor_names.get(i, f'Factor_{i+1}') if factor_names else None
            }

        return interpretation

    def analyze_indicator_importance(
        self,
        high_threshold: float = 0.7,
        medium_threshold: float = 0.4,
        top_n: int = 10
    ) -> Dict[str, Dict]:
        """
        分析各指标的重要性

        通过因子载荷矩阵分析每个指标对因子的贡献程度，
        帮助识别关键指标和冗余指标。

        Parameters
        ----------
        high_threshold : float
            高贡献阈值（载荷绝对值），默认0.7
        medium_threshold : float
            中等贡献阈值（载荷绝对值），默认0.4
        top_n : int
            返回每个因子的top N指标

        Returns
        -------
        importance_analysis : dict
            {
                'by_factor': {
                    'Factor_1': {
                        'high_contribution': [...],  # 载荷>0.7的指标
                        'medium_contribution': [...], # 载荷0.4-0.7
                        'low_contribution': [...],    # 载荷<0.4（可考虑删除）
                    }
                },
                'overall_importance': {
                    '指标名称': {
                        'max_loading': 0.85,          # 最大载荷（在哪个因子上）
                        'max_loading_factor': 'Factor_1',
                        'mean_loading': 0.45,         # 平均载荷
                        'rank': 1                     # 重要性排名
                    }
                },
                'redundant_indicators': [...],  # 在所有因子上载荷都很低的指标
                'key_indicators': [...]         # 在某个因子上载荷很高的指标
            }
        """
        if not hasattr(self, 'pca_model'):
            raise ValueError("模型尚未拟合，请先调用fit()方法")

        # 获取因子载荷矩阵
        loadings = self.get_factor_loadings()

        # 初始化结果字典
        importance_analysis = {
            'by_factor': {},
            'overall_importance': {},
            'redundant_indicators': [],
            'key_indicators': []
        }

        # 遍历每个因子，分析指标贡献
        for factor_name in loadings.columns:
            factor_loadings = loadings[factor_name]
            absolute_loadings = factor_loadings.abs()

            # 分类指标贡献度
            high_contribution = absolute_loadings[absolute_loadings >= high_threshold]
            medium_contribution = absolute_loadings[
                (absolute_loadings >= medium_threshold) &
                (absolute_loadings < high_threshold)
            ]
            low_contribution = absolute_loadings[absolute_loadings < medium_threshold]

            # 保存每个因子的指标分类
            importance_analysis['by_factor'][factor_name] = {
                'high_contribution': {
                    'indicators': high_contribution.index.tolist(),
                    'loadings': high_contribution.round(4).to_dict()
                },
                'medium_contribution': {
                    'indicators': medium_contribution.index.tolist(),
                    'loadings': medium_contribution.round(4).to_dict()
                },
                'low_contribution': {
                    'indicators': low_contribution.index.tolist(),
                    'loadings': low_contribution.round(4).to_dict()
                }
            }

        # 计算整体指标重要性
        max_loadings = loadings.abs().max(axis=1)
        max_loading_factors = loadings.abs().idxmax(axis=1)
        mean_loadings = loadings.abs().mean(axis=1)

        overall_importance = pd.DataFrame({
            'max_loading': max_loadings,
            'max_loading_factor': max_loading_factors,
            'mean_loading': mean_loadings
        }).sort_values('max_loading', ascending=False)

        overall_importance['rank'] = range(1, len(overall_importance) + 1)

        # 转换为字典格式
        for indicator in overall_importance.index:
            importance_analysis['overall_importance'][indicator] = {
                'max_loading': round(overall_importance.loc[indicator, 'max_loading'], 4),
                'max_loading_factor': overall_importance.loc[indicator, 'max_loading_factor'],
                'mean_loading': round(overall_importance.loc[indicator, 'mean_loading'], 4),
                'rank': int(overall_importance.loc[indicator, 'rank'])
            }

        # 识别关键指标和冗余指标
        key_indicators = max_loadings[max_loadings >= high_threshold].index.tolist()
        redundant_indicators = max_loadings[max_loadings < medium_threshold].index.tolist()

        importance_analysis['key_indicators'] = key_indicators
        importance_analysis['redundant_indicators'] = redundant_indicators

        # 打印摘要信息
        print(f"\n{'='*60}")
        print(f"指标重要性分析")
        print(f"{'='*60}")
        print(f"总指标数：{len(loadings)}")
        print(f"关键指标数（载荷≥{high_threshold}）：{len(key_indicators)}")
        print(f"冗余指标数（载荷<{medium_threshold}）：{len(redundant_indicators)}")
        print(f"关键指标：{key_indicators}")
        if redundant_indicators:
            print(f"冗余指标：{redundant_indicators}")
        print(f"{'='*60}\n")

        return importance_analysis

    def plot_indicator_importance(
        self,
        factor_index: int = 0,
        top_n: int = 15,
        figsize: Tuple[int, int] = (10, 8)
    ):
        """
        绘制指标重要性排序图（水平条形图）

        Parameters
        ----------
        factor_index : int
            因子索引（0, 1, 2...）
        top_n : int
            显示前N个最重要的指标
        figsize : tuple
            图形大小

        Returns
        -------
        fig : matplotlib.figure.Figure
        """
        import matplotlib.pyplot as plt

        if not hasattr(self, 'pca_model'):
            raise ValueError("模型尚未拟合，请先调用fit()方法")

        # 获取因子载荷
        loadings = self.get_factor_loadings()
        factor_name = f'Factor_{factor_index + 1}'

        # 载荷绝对值排序
        loadings_abs = loadings[factor_name].abs().sort_values(ascending=True)
        top_loadings = loadings_abs.tail(top_n)

        # 绘制水平条形图
        fig, ax = plt.subplots(figsize=figsize)

        colors = ['#d7191c' if x >= 0.7 else '#fdae61' if x >= 0.4 else '#abd9e9'
                  for x in top_loadings.values]

        top_loadings.plot(kind='barh', color=colors, ax=ax)
        ax.set_xlabel(f'因子载荷绝对值', fontsize=12)
        ax.set_ylabel(f'指标名称', fontsize=12)
        ax.set_title(f'因子 {factor_name} - 指标重要性排序（Top {top_n}）', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')

        # 添加图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#d7191c', label=f'高贡献 (≥0.7)'),
            Patch(facecolor='#fdae61', label=f'中贡献 (0.4-0.7)'),
            Patch(facecolor='#abd9e9', label=f'低贡献 (<0.4)')
        ]
        ax.legend(handles=legend_elements, loc='lower right')

        plt.tight_layout()
        return fig

    def plot_factors(self, figsize: Tuple[int, int] = (12, 8)):
        """
        绘制因子时序图

        Parameters
        ----------
        figsize : tuple
            图形大小
        """
        import matplotlib.pyplot as plt

        if self.factors is None:
            raise ValueError("模型尚未拟合")

        fig, axes = plt.subplots(self.n_factors, 1, figsize=figsize, sharex=True)

        if self.n_factors == 1:
            axes = [axes]

        for i, ax in enumerate(axes):
            factor_name = self.factors.columns[i]
            ax.plot(self.factors.index, self.factors.iloc[:, i])
            ax.set_title(factor_name)
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def get_factor_stability(
        self,
        window: int = 252
    ) -> pd.DataFrame:
        """
        检验因子稳定性（滚动窗口相关系数）

        Parameters
        ----------
        window : int
            滚动窗口大小（约1年交易日）

        Returns
        -------
        pd.DataFrame
            滚动相关系数矩阵
        """
        if self.factors is None:
            raise ValueError("模型尚未拟合")

        # 计算滚动相关系数
        rolling_corr = self.factors.rolling(window=window).corr()

        return rolling_corr


class SparseDFM(BaseDFM):
    """
    稀疏动态因子模型

    改进：通过正则化使载荷矩阵更稀疏，提高模型可解释性
    """

    def __init__(
        self,
        n_factors: int = 3,
        factor_orders: int = 2,
        alpha: float = 1.0,
        l1_ratio: float = 0.5,
        standardize: bool = True
    ):
        """
        参数
        ----
        alpha : float
            正则化强度
        l1_ratio : float
            L1正则化比例（0表示仅L2，1表示仅L1）
        """
        super().__init__(n_factors, factor_orders, standardize)
        self.alpha = alpha
        self.l1_ratio = l1_ratio

    def fit_pca(
        self,
        data: pd.DataFrame,
        n_factors: Optional[int] = None
    ) -> Tuple[pd.DataFrame, object]:
        """
        使用稀疏PCA提取因子
        """
        from sklearn.decomposition import SparsePCA

        if n_factors is None:
            n_factors = self.n_factors

        sparse_pca = SparsePCA(
            n_components=n_factors,
            alpha=self.alpha,
            l1_ratio=self.l1_ratio,
            max_iter=1000,
            random_state=42
        )

        factors = sparse_pca.fit_transform(data)

        factor_names = [f'Factor_{i+1}' for i in range(n_factors)]
        factors_df = pd.DataFrame(
            factors,
            index=data.index,
            columns=factor_names
        )

        return factors_df, sparse_pca
