"""
中国宏观经济周期识别模型（独立实现）

基于马尔可夫区制转移模型识别中国宏观状态：
1. 复苏（Recovery）
2. 过热（Overheat）
3. 滞胀（Stagflation）
4. 衰退（Recession）

特点：
- 完全独立实现，不依赖基类
- 支持月度数据
- 政策驱动型特征
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

from models.dfm.cn_dfm import CNDFM

try:
    from hmmlearn import hmm
    HMMLEARN_AVAILABLE = True
except ImportError:
    HMMLEARN_AVAILABLE = False
    print("警告：hmmlearn不可用，将使用statsmodels")


class CNPolicyRegimeModel:
    """
    中国宏观状态识别模型（独立实现）

    输入：
    - 经济增长因子
    - 通胀因子
    - 流动性因子

    输出：
    - 每日的宏观状态概率
    - 最可能的宏观状态
    """

    # 区制名称定义
    REGIME_NAMES = {
        'Regime_1': '复苏',
        'Regime_2': '过热',
        'Regime_3': '滞胀',
        'Regime_4': '衰退'
    }

    # 中国特色政策周期（用于验证）
    POLICY_CYCLES = {
        '2008-2009': ('2008-11', '2009-12'),  # 四万亿刺激
        '2015-2016': ('2015-01', '2016-12'),  # 供给侧改革
        '2020-2021': ('2020-01', '2021-12'),  # 疫情后复苏
    }

    def __init__(self, n_regimes: int = 4):
        """
        初始化中国区制模型

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

        # 加载中国DFM模型
        self.dfm_model = CNDFM(n_factors=3)

    def fit_with_factors(
        self,
        growth_factor: pd.Series,
        inflation_factor: pd.Series,
        liquidity_factor: pd.Series
    ) -> 'CNPolicyRegimeModel':
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

            # 根据因子特征判断经济含义
            if growth_mean > 0 and inflation_mean < 0:
                economic_meaning = '复苏'
                description = "复苏：经济增长上升，通胀温和"
            elif growth_mean > 0 and inflation_mean > 0:
                economic_meaning = '过热'
                description = "过热：经济增长强劲，通胀压力较大"
            elif growth_mean < 0 and inflation_mean > 0:
                economic_meaning = '滞胀'
                description = "滞胀：经济疲弱，通胀高企"
            elif growth_mean < 0 and inflation_mean < 0:
                economic_meaning = '衰退'
                description = "衰退：经济收缩，通胀下行"
            else:
                economic_meaning = '过渡期'
                description = "过渡期"

            interpretation[regime] = {
                'economic_meaning': economic_meaning,
                'growth_factor_mean': growth_mean,
                'inflation_factor_mean': inflation_mean,
                'description': description
            }

        return interpretation

    def interpret_with_policy(self) -> Dict[str, Dict]:
        """
        基于政策环境解释区制（中国特有）

        Returns
        -------
        interpretation : dict
            政策环境解释
        """
        if self.liquidity_factor is None:
            raise ValueError("需要先使用fit_with_factors()方法")

        interpretation = {}

        for regime in [f'Regime_{i+1}' for i in range(self.n_regimes)]:
            regime_periods = self.regime_sequence == regime

            if regime_periods.sum() == 0:
                continue

            # 计算流动性因子均值（M2增长代理）
            liquidity_mean = self.liquidity_factor[regime_periods].mean()
            growth_mean = self.growth_factor[regime_periods].mean()

            # 基于流动性判断政策环境
            if liquidity_mean > 0.5:
                policy_stance = "宽松"
                policy_description = "货币政策宽松，流动性充裕"
            elif liquidity_mean < -0.5:
                policy_stance = "紧缩"
                policy_description = "货币政策紧缩，流动性收紧"
            else:
                policy_stance = "中性"
                policy_description = "货币政策中性"

            interpretation[regime] = {
                'policy_stance': policy_stance,
                'liquidity_factor_mean': liquidity_mean,
                'policy_description': policy_description,
                'growth_mean': growth_mean
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

    def validate_with_policy_cycles(self) -> Dict[str, Dict]:
        """
        使用中国政策周期验证模型准确性

        Returns
        -------
        results : dict
            验证结果
        """
        print("\n[验证] 与中国政策周期对比...")

        results = {}

        for cycle_name, (start, end) in self.POLICY_CYCLES.items():
            # 找出模型识别的扩张期（复苏+过热）
            expansion_periods = self.regime_sequence.isin(['Regime_1', 'Regime_2'])

            # 检查政策周期是否被识别
            policy_dates = pd.date_range(start, end, freq='M')
            # 只保留在数据索引内的日期
            policy_dates = policy_dates[policy_dates.isin(self.regime_sequence.index)]

            if len(policy_dates) == 0:
                continue

            identified = sum(expansion_periods.loc[policy_dates])
            total = len(policy_dates)
            accuracy = identified / total if total > 0 else 0

            results[cycle_name] = {
                'policy_dates': (start, end),
                'identified_periods': int(identified),
                'total_periods': total,
                'accuracy': accuracy
            }

            print(f"\n{cycle_name}（{start} 至 {end}）：")
            print(f"  模型识别：{identified}/{total} 个月")
            print(f"  准确率：{accuracy:.2%}")

        return results

    def export_regime_data(self, output_path: str = 'models/regime/cn_regime_data.csv'):
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
def load_cn_regime_model(
    csv_path: str = 'data/processed/china/all_indicators_extended.csv',
    start_date: str = '1950-01-01',
    n_regimes: int = 4
) -> CNPolicyRegimeModel:
    """
    快速加载并训练中国区制模型

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
    model : CNPolicyRegimeModel
        训练好的模型
    """
    import pandas as pd

    model = CNPolicyRegimeModel(n_regimes=n_regimes)
    dfm = CNDFM(n_factors=3)

    # 加载数据
    print("正在加载数据...")
    cn_data = pd.read_csv(csv_path, encoding='utf-8-sig')
    cn_data['date'] = pd.to_datetime(cn_data['date'])

    # 过滤日期范围
    cn_data = cn_data[cn_data['date'] >= start_date].copy()

    # 选择月度数据
    monthly_data = cn_data[cn_data['frequency'] == 'm'].copy()

    # 转为宽表格式
    monthly_wide = monthly_data.pivot(
        index='date',
        columns='indicator_code',
        values='value'
    )

    # 过滤缺失值过多的列
    missing_stats = monthly_wide.isnull().sum() / len(monthly_wide) * 100
    valid_cols = missing_stats[missing_stats < 60].index
    monthly_clean = monthly_wide[valid_cols]

    # 前向/后向填充
    monthly_filled = monthly_clean.ffill().bfill().dropna()

    print(f"从CSV加载 {len(monthly_filled.columns)} 个指标，{len(monthly_filled)} 个时间点")
    print(f"数据时间范围：{monthly_filled.index.min()} 至 {monthly_filled.index.max()}")

    # 提取因子
    print("正在提取因子...")
    dfm.fit(monthly_filled, method='pca')
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
    print("测试中国区制模型（独立实现）")
    print("="*60)

    model = load_cn_regime_model(
        csv_path='data/processed/china/all_indicators_extended.csv',
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

    # 政策环境解释
    print(f"\n政策环境解释：")
    policy_interp = model.interpret_with_policy()
    for regime, info in policy_interp.items():
        print(f"\n{regime}: {info['policy_stance']}")
        print(f"  描述：{info['policy_description']}")
        print(f"  流动性因子均值：{info['liquidity_factor_mean']:.2f}")
