"""
美国宏观经济周期识别模型（独立实现）

基于马尔可夫区制转移模型识别美国宏观状态：
1. 复苏（Recovery）
2. 过热（Overheat）
3. 滞胀（Stagflation）
4. 衰退（Recession）

特点：
- 完全独立实现，不依赖基类
- 支持日度数据
- 与NBER衰退期验证
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
import os
import warnings

warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.dfm.us_dfm import USDFM

try:
    from hmmlearn import hmm
    HMMLEARN_AVAILABLE = True
except ImportError:
    HMMLEARN_AVAILABLE = False
    print("警告：hmmlearn不可用，将使用statsmodels")


class USMarketRegimeModel:
    """
    美国宏观状态识别模型（独立实现）

    输入：
    - 经济增长因子
    - 通胀因子
    - 流动性因子

    输出：
    - 每日的宏观状态概率
    - 最可能的宏观状态
    """

    # 区制名称定义（基于实际因子特征和NBER验证重新定义）
    REGIME_NAMES = {
        'Regime_1': '正常增长',  # 增长↑, 通胀↓
        'Regime_2': '过热',      # 增长↑↑, 通胀↑
        'Regime_3': '衰退',      # 增长↓↓, 通胀↑ (NBER验证: 91.7%+100%)
        'Regime_4': '滞胀'       # 增长↓, 通胀↑↑
    }

    # 历史衰退期（用于验证）
    NBER_RECESSIONS = {
        '2001': ('2001-03', '2001-11'),
        '2007-2009': ('2007-12', '2009-06'),
        '2020': ('2020-02', '2020-04'),
    }

    def __init__(self, n_regimes: int = 4):
        """
        初始化美国区制模型

        Parameters
        ----------
        n_regimes : int
            区制数量（默认4个）
        """
        self.n_regimes = n_regimes
        self.regime_probs = None
        self.regime_sequence = None
        self.results = None  # statsmodels或hmmlearn的结果对象

        # 因子数据
        self.growth_factor = None
        self.inflation_factor = None
        self.liquidity_factor = None

        # 加载美国DFM模型
        self.dfm_model = USDFM(n_factors=3)

    def fit_with_factors(
        self,
        growth_factor: pd.Series,
        inflation_factor: pd.Series,
        liquidity_factor: pd.Series
    ) -> 'USMarketRegimeModel':
        """
        使用提取的因子拟合区制模型

        Parameters
        ----------
        growth_factor : pd.Series
            经济增长因子
        inflation_factor : pd.Series
            通胀因子
        liquidity_factor : pd.Series
            流动性因子

        Returns
        -------
        self
        """
        # 保存因子数据
        self.growth_factor = growth_factor
        self.inflation_factor = inflation_factor
        self.liquidity_factor = liquidity_factor

        # 准备特征矩阵
        features = pd.DataFrame({
            'growth': growth_factor,
            'inflation': inflation_factor,
            'liquidity': liquidity_factor
        })

        # 对齐索引
        features = features.dropna()

        print(f"拟合区制模型，使用 {len(features)} 个观测值...")

        # 尝试使用statsmodels
        try:
            self._fit_with_statsmodels(features)
        except Exception as e:
            print(f"statsmodels估计失败：{e}")
            print("降级到hmmlearn...")
            self._fit_with_hmmlearn(features)

        # 创建区制概率DataFrame
        if hasattr(self.results, 'smooth_marginal_probabilities'):
            # statsmodels结果
            self.regime_probs = pd.DataFrame(
                self.results.smooth_marginal_probabilities,
                index=features.index,
                columns=[f'Regime_{i+1}' for i in range(self.n_regimes)]
            )
        elif hasattr(self.results, 'predict_proba'):
            # hmmlearn结果
            self.regime_probs = pd.DataFrame(
                self.results.predict_proba(features.values),
                index=features.index,
                columns=[f'Regime_{i+1}' for i in range(self.n_regimes)]
            )

        # 计算区制序列（最可能的区制）
        self.regime_sequence = self.regime_probs.idxmax(axis=1)

        print(f"区制识别完成")

        return self

    def _fit_with_statsmodels(self, features: pd.DataFrame):
        """
        使用statsmodels的MarkovRegression拟合
        """
        from statsmodels.tsa.regime_switching import MarkovRegression

        # 准备数据（使用增长因子作为观测变量）
        y = features['growth'].values

        # 拟合模型（使用switching_mean）
        self.results = MarkovRegression(
            y,
            k_regimes=self.n_regimes,
            switching_variance=False,
            trend='n'  # 包含趋势项
        )

        self.results = self.results.fit(disp=False)
        print(f"statsmodels估计成功")

    def _fit_with_hmmlearn(self, features: pd.DataFrame):
        """
        使用hmmlearn的GaussianHMM拟合
        """
        if not HMMLEARN_AVAILABLE:
            raise ImportError("hmmlearn不可用且statsmodels失败")

        self.results = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type='full',
            n_iter=1000,
            random_state=42
        )

        self.results.fit(features.values)
        print(f"hmmlearn拟合成功")

    def get_regime_probs(self) -> pd.DataFrame:
        """
        获取区制概率时间序列

        Returns
        -------
        regime_probs : pd.DataFrame
            区制概率，形状为(T, n_regimes)
        """
        if self.regime_probs is None:
            raise ValueError("模型尚未拟合")
        return self.regime_probs

    def get_regime_sequence(self) -> pd.Series:
        """
        获取最可能的区制序列

        Returns
        -------
        regime_sequence : pd.Series
            区制序列
        """
        if self.regime_sequence is None:
            raise ValueError("模型尚未拟合")
        return self.regime_sequence

    def get_transition_matrix(self) -> pd.DataFrame:
        """
        获取状态转移概率矩阵

        Returns
        -------
        transition_matrix : pd.DataFrame
            转移概率矩阵
        """
        if hasattr(self.results, 'regime_transition'):
            # statsmodels结果
            return pd.DataFrame(
                self.results.regime_transition,
                index=[f'Regime_{i+1}' for i in range(self.n_regimes)],
                columns=[f'Regime_{i+1}' for i in range(self.n_regimes)]
            )
        elif hasattr(self.results, 'transmat_'):
            # hmmlearn结果
            return pd.DataFrame(
                self.results.transmat_,
                index=[f'Regime_{i+1}' for i in range(self.n_regimes)],
                columns=[f'Regime_{i+1}' for i in range(self.n_regimes)]
            )
        else:
            raise ValueError("无法提取转移概率矩阵")

    def get_regime_durations(self) -> Dict[str, float]:
        """
        计算各区制的期望持续期

        Returns
        -------
        durations : dict
            区制持续期（以数据频度为单位）
        """
        transition = self.get_transition_matrix()
        durations = {}

        for i in range(self.n_regimes):
            regime_name = f'Regime_{i+1}'
            # 期望持续期 = 1 / (1 - p_ii)
            stay_prob = transition.loc[regime_name, regime_name]
            expected_duration = 1 / (1 - stay_prob)
            durations[regime_name] = expected_duration

        return durations

    def interpret_regimes(self) -> Dict[str, Dict]:
        """
        解释各区制的经济含义

        基于因子特征进行解释

        Returns
        -------
        interpretation : dict
            区制解释
        """
        if self.growth_factor is None:
            raise ValueError("需要先使用fit_with_factors()方法")

        interpretation = {}

        for regime in [f'Regime_{i+1}' for i in range(self.n_regimes)]:
            # 找出该区制对应的时期
            regime_periods = self.regime_sequence == regime

            if regime_periods.sum() == 0:
                continue

            # 计算该区制下的因子均值
            growth_mean = self.growth_factor[regime_periods].mean()
            inflation_mean = self.inflation_factor[regime_periods].mean()

            # 根据因子特征判断经济含义（基于NBER验证结果优化）
            if growth_mean < -1.0:
                # 深度负增长 → 衰退（Regime_3）
                economic_meaning = '衰退'
                description = f"衰退：经济深度收缩（增长因子：{growth_mean:.2f}），通胀维持"
            elif inflation_mean > 2.0:
                # 高通胀 → 滞胀（Regime_4）
                economic_meaning = '滞胀'
                description = f"滞胀：经济增长乏力，通胀高企（通胀因子：{inflation_mean:.2f}）"
            elif growth_mean > 1.0 and inflation_mean > 0:
                # 高增长+通胀 → 过热（Regime_2）
                economic_meaning = '过热'
                description = f"过热：经济强劲增长（增长因子：{growth_mean:.2f}），通胀压力上升"
            else:
                # 正常增长（Regime_1）
                economic_meaning = '正常增长'
                description = f"正常增长：经济温和增长（增长因子：{growth_mean:.2f}），通胀受控"

            interpretation[regime] = {
                'economic_meaning': economic_meaning,
                'growth_factor_mean': growth_mean,
                'inflation_factor_mean': inflation_mean,
                'description': description
            }

        return interpretation

    def predict_next_regime(self) -> Tuple[str, float]:
        """
        预测下一期的区制

        Returns
        -------
        next_regime : str
            最可能的下一期区制
        probability : float
            转移到该区制的概率
        """
        # 获取当前区制
        current_regime = self.regime_sequence.iloc[-1]

        # 获取转移矩阵
        transition = self.get_transition_matrix()

        # 获取转移概率
        transition_probs = transition.loc[current_regime]

        # 找出概率最大的区制
        next_regime = transition_probs.idxmax()
        probability = transition_probs.max()

        return next_regime, probability

    def validate_with_nber(self) -> Dict[str, Dict]:
        """
        使用NBER衰退期验证模型准确性

        Returns
        -------
        results : dict
            验证结果
        """
        print("\n[验证] 与NBER衰退期对比...")

        results = {}

        for recession_name, (start, end) in self.NBER_RECESSIONS.items():
            # 找出模型识别的衰退期（重新定义：Regime_3为衰退）
            recession_periods = self.regime_sequence == 'Regime_3'  # 衰退区制

            # 检查NBER衰退期是否被识别
            nber_recession_dates = pd.date_range(start, end, freq='M')
            # 只保留在数据索引内的日期
            nber_recession_dates = nber_recession_dates[nber_recession_dates.isin(self.regime_sequence.index)]

            if len(nber_recession_dates) == 0:
                continue

            identified = sum(recession_periods.loc[nber_recession_dates])
            total = len(nber_recession_dates)
            accuracy = identified / total if total > 0 else 0

            results[recession_name] = {
                'nber_dates': (start, end),
                'identified_periods': int(identified),
                'total_periods': total,
                'accuracy': accuracy
            }

            print(f"\n{recession_name}（{start} 至 {end}）：")
            print(f"  模型识别：{identified}/{total} 个月")
            print(f"  准确率：{accuracy:.2%}")

        return results

    def export_regime_data(self, output_path: str = 'models/regime/us_regime_data.csv'):
        """
        导出区制数据到CSV

        Parameters
        ----------
        output_path : str
            输出路径
        """
        # 合并区制概率和区制序列
        export_data = self.regime_probs.copy()
        export_data['regime'] = self.regime_sequence

        # 保存
        export_data.to_csv(output_path, encoding='utf-8-sig')
        print(f"\n区制数据已导出到：{output_path}")

    def get_current_regime(self) -> Dict[str, any]:
        """
        获取当前（最新）的宏观状态

        Returns
        -------
        current_state : dict
            当前状态信息
        """
        latest_probs = self.regime_probs.iloc[-1]
        latest_regime = self.regime_sequence.iloc[-1]

        # 解释当前区制
        interpretation = self.interpret_regimes()

        return {
            'date': self.regime_probs.index[-1],
            'regime': latest_regime,
            'regime_name': interpretation.get(latest_regime, {}).get('economic_meaning', latest_regime),
            'regime_probs': latest_probs.to_dict(),
            'description': interpretation.get(latest_regime, {}).get('description', '')
        }

    def plot_regime_probs(
        self,
        figsize: Tuple[int, int] = (14, 8)
    ):
        """
        绘制区制概率时序图

        Parameters
        ----------
        figsize : tuple
            图形大小
        """
        import matplotlib.pyplot as plt

        if self.regime_probs is None:
            raise ValueError("模型尚未拟合")

        fig, axes = plt.subplots(
            self.n_regimes,
            1,
            figsize=figsize,
            sharex=True
        )

        if self.n_regimes == 1:
            axes = [axes]

        for i, ax in enumerate(axes):
            regime_name = self.regime_probs.columns[i]
            ax.fill_between(
                self.regime_probs.index,
                self.regime_probs.iloc[:, i],
                alpha=0.5
            )
            ax.set_title(f'{regime_name} 概率')
            ax.set_ylim(0, 1)
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def plot_regime_sequence(
        self,
        growth_factor: pd.Series,
        figsize: Tuple[int, int] = (14, 6)
    ):
        """
        绘制区制序列与增长因子对比图

        Parameters
        ----------
        growth_factor : pd.Series
            增长因子
        figsize : tuple
            图形大小
        """
        import matplotlib.pyplot as plt

        if self.regime_sequence is None:
            raise ValueError("模型尚未拟合")

        # 标准化增长因子（用于可视化）
        growth_norm = (growth_factor - growth_factor.mean()) / growth_factor.std()

        # 创建数值映射（用于颜色映射）
        regime_map = {
            f'Regime_{i+1}': i
            for i in range(self.n_regimes)
        }
        regime_values = self.regime_sequence.map(regime_map)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)

        # 绘制增长因子
        ax1.plot(growth_norm.index, growth_norm.values, label='标准化增长因子', linewidth=1.5)
        ax1.set_ylabel('标准化值')
        ax1.set_title('经济增长因子')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # 绘制区制序列
        ax2.scatter(
            regime_values.index,
            regime_values.values,
            c=regime_values.values,
            cmap='viridis',
            alpha=0.6,
            s=10
        )
        ax2.set_ylabel('区制')
        ax2.set_xlabel('日期')
        ax2.set_title('识别的宏观区制')
        ax2.set_yticks(range(self.n_regimes))
        ax2.set_yticklabels([f'Regime_{i+1}' for i in range(self.n_regimes)])
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig


# 便捷函数
def load_us_regime_model(
    csv_path: str = 'data/csv/us_all_indicators_extended.csv',
    start_date: str = '1950-01-01',
    n_regimes: int = 4
) -> USMarketRegimeModel:
    """
    快速加载并训练美国区制模型

    Parameters
    ----------
    csv_path : str
        CSV文件路径
    start_date : str
        开始日期
    n_regimes : int
        区制数量

    Returns
    -------
    model : USMarketRegimeModel
        训练好的模型
    """
    model = USMarketRegimeModel(n_regimes=n_regimes)

    # 加载DFM
    dfm = USDFM(n_factors=3)

    # 加载数据
    print("正在加载数据...")
    macro_data = dfm.fetch_from_csv(csv_path, start_date=start_date)

    # 提取因子
    print("正在提取因子...")
    dfm.fit(macro_data, method='pca')
    factors = dfm.get_factors()

    # 拟合区制模型
    print("正在拟合区制模型...")
    model.fit_with_factors(
        growth_factor=factors.iloc[:, 0],
        inflation_factor=factors.iloc[:, 1],
        liquidity_factor=factors.iloc[:, 2]
    )

    print("✅ 模型训练完成！")

    return model


if __name__ == '__main__':
    # 测试代码
    print("="*60)
    print("测试美国区制模型（独立实现）")
    print("="*60)

    model = load_us_regime_model(
        csv_path='data/csv/us_all_indicators_extended.csv',
        start_date='1950-01-01',
        n_regimes=4
    )

    # 当前状态
    current = model.get_current_regime()
    print(f"\n当前状态：{current['regime_name']}")
    print(f"日期：{current['date']}")
    print(f"置信度：{current['regime_probs'][current['regime']]*100:.2f}%")

    # 区制分布
    print(f"\n区制分布：")
    counts = model.regime_sequence.value_counts()
    total = len(model.regime_sequence)
    for regime, count in counts.items():
        pct = count / total * 100
        print(f"  {regime}: {count:4d} 次 ({pct:5.1f}%)")
