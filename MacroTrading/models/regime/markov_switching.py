"""
马尔可夫区制转移模型（Markov-Switching Model）

理论基础：
1. 宏观经济存在多个状态（区制）：复苏、过热、滞胀、衰退
2. 状态之间的转移服从马尔可夫过程
3. 不同状态下，变量具有不同的统计特征

应用场景：
- 经济周期识别
- 衰退预测
- 资产配置（不同状态下资产表现不同）

参考文献：
- Hamilton, J. D. (1989). A new approach to the economic analysis of nonstationary time series and the business cycle.
- Kim, C. J., & Nelson, C. R. (1999). State-space models with regime switching.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Tuple, Union
import warnings

# statsmodels的马尔可夫转移模型
from statsmodels.tsa.regime_switching.markov_switching import MarkovSwitching
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

# hmmlearn作为备选方案
from hmmlearn import hmm

warnings.filterwarnings('ignore')


class BaseMarkovSwitching:
    """
    马尔可夫区制转移模型基类

    核心思想：
    y_t = μ_{s_t} + ε_t
    s_t ∈ {1, 2, ..., K}  （K个状态）
    P(s_t = j | s_{t-1} = i) = p_{ij}  （转移概率矩阵）

    其中：
    - y_t: 观测变量（如GDP增长率）
    - s_t: 不可观测的状态变量
    - μ_{s_t}: 状态s_t下的均值
    - p_{ij}: 从状态i转移到状态j的概率
    """

    def __init__(
        self,
        n_regimes: int = 4,
        switching_mean: bool = True,
        switching_var: bool = False,
        trend: bool = False
    ):
        """
        初始化马尔可夫转移模型

        Parameters
        ----------
        n_regimes : int
            区制数量（默认4个：复苏、过热、滞胀、衰退）
        switching_mean : bool
            是否允许均值在不同区制间切换
        switching_var : bool
            是否允许方差在不同区制间切换
        trend : bool
            是否包含趋势项
        """
        self.n_regimes = n_regimes
        self.switching_mean = switching_mean
        self.switching_var = switching_var
        self.trend = trend

        self.model = None
        self.results = None
        self.regime_probs = None
        self.regime_sequence = None

    def fit(
        self,
        data: pd.Series,
        method: str = 'statsmodels'
    ) -> 'BaseMarkovSwitching':
        """
        拟合马尔可夫转移模型

        Parameters
        ----------
        data : pd.Series
            时间序列数据
        method : str
            估计方法：'statsmodels' 或 'hmmlearn'

        Returns
        -------
        self
        """
        if method == 'statsmodels':
            self._fit_statsmodels(data)
        elif method == 'hmmlearn':
            self._fit_hmmlearn(data)
        else:
            raise ValueError(f"未知的估计方法：{method}")

        return self

    def _fit_statsmodels(self, data: pd.Series):
        """
        使用statsmodels估计马尔可夫转移模型
        """
        try:
            # 创建MarkovRegression模型
            self.model = MarkovRegression(
                endog=data.values,
                k_regimes=self.n_regimes,
                switching_mean=self.switching_mean,
                switching_var=self.switching_var,
                trend='c' if not self.trend else 't'
            )

            # 估计模型
            self.results = self.model.fit(
                maxiter=100,
                search_reps=20,
                em_iter=20
            )

            # 提取平滑后的状态概率
            self.regime_probs = pd.DataFrame(
                self.results.smoothed_marginal_probabilities,
                index=data.index,
                columns=[f'Regime_{i+1}' for i in range(self.n_regimes)]
            )

            # 提取最可能的状态序列
            self.regime_sequence = self.regime_probs.idxmax(axis=1)

        except Exception as e:
            print(f"statsmodels估计失败：{e}")
            print("降级到hmmlearn...")
            self._fit_hmmlearn(data)

    def _fit_hmmlearn(self, data: pd.Series):
        """
        使用hmmlearn估计HMM模型（备选方案）
        """
        # 准备数据
        X = data.values.reshape(-1, 1)

        # 标准化
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 创建GaussianHMM模型
        model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type="full",
            n_iter=1000,
            random_state=42
        )

        # 拟合模型
        model.fit(X_scaled)

        # 获取隐状态序列
        hidden_states = model.predict(X_scaled)

        # 获取状态概率
        regime_probs = model.predict_proba(X_scaled)

        # 保存结果
        self.model = model
        self.results = model
        self.regime_probs = pd.DataFrame(
            regime_probs,
            index=data.index,
            columns=[f'Regime_{i+1}' for i in range(self.n_regimes)]
        )
        self.regime_sequence = pd.Series(
            [f'Regime_{i+1}' for i in hidden_states],
            index=data.index
        )

    def get_regime_probs(self) -> pd.DataFrame:
        """
        获取各时期的区制概率

        Returns
        -------
        pd.DataFrame
            区制概率（时间 x 区制）
        """
        if self.regime_probs is None:
            raise ValueError("模型尚未拟合")
        return self.regime_probs

    def get_regime_sequence(self) -> pd.Series:
        """
        获取最可能的区制序列

        Returns
        -------
        pd.Series
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
        pd.DataFrame
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
        dict
            区制持续期
        """
        transition = self.get_transition_matrix()
        durations = {}

        for i in range(self.n_regimes):
            regime_name = f'Regime_{i+1}'
            # 期望持续期 = 1 / (1 - p_ii)
            # 其中p_ii是停留在当前状态的概率
            stay_prob = transition.loc[regime_name, regime_name]
            expected_duration = 1 / (1 - stay_prob)
            durations[regime_name] = expected_duration

        return durations

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
        data: Optional[pd.Series] = None,
        figsize: Tuple[int, int] = (14, 6)
    ):
        """
        绘制区制序列（与原始数据对比）

        Parameters
        ----------
        data : pd.Series, optional
            原始数据
        figsize : tuple
            图形大小
        """
        fig, axes = plt.subplots(
            2 if data is not None else 1,
            1,
            figsize=figsize,
            sharex=True
        )

        if data is not None:
            axes[0].plot(data.index, data.values)
            axes[0].set_title('原始数据')
            axes[0].grid(True, alpha=0.3)

            # 绘制区制
            ax = axes[1]
        else:
            ax = axes

        # 将区制转换为数值
        regime_map = {f'Regime_{i+1}': i for i in range(self.n_regimes)}
        regime_numeric = self.regime_sequence.map(regime_map)

        ax.plot(regime_numeric.index, regime_numeric.values, drawstyle='steps-post')
        ax.set_yticks(range(self.n_regimes))
        ax.set_yticklabels([f'Regime_{i+1}' for i in range(self.n_regimes)])
        ax.set_title('区制识别结果')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def predict_next_regime(self) -> Tuple[str, float]:
        """
        预测下一期的最可能区制

        Returns
        -------
        regime : str
            最可能的区制
        prob : float
            概率
        """
        # 获取最后一期的区制概率
        last_probs = self.regime_probs.iloc[-1]

        # 获取转移概率矩阵
        transition = self.get_transition_matrix()

        # 计算下一期的区制概率
        next_probs = last_probs.values @ transition.values

        # 找出最可能的区制
        next_regime_idx = np.argmax(next_probs)
        next_regime = f'Regime_{next_regime_idx+1}'
        next_prob = next_probs[next_regime_idx]

        return next_regime, next_prob


class MacroRegimeModel(BaseMarkovSwitching):
    """
    宏观经济周期识别模型

    四个区制：
    1. 复苏（Recovery）：增长上升，通胀温和
    2. 过热（Overheat）：增长高，通胀高
    3. 滞胀（Stagflation）：增长低，通胀高
    4. 衰退（Recession）：增长下降，通胀下降

    使用因子进行识别：
    - 经济增长因子
    - 通胀因子
    - 流动性因子
    """

    # 区制定义
    REGIME_NAMES = {
        'Regime_1': '复苏',
        'Regime_2': '过热',
        'Regime_3': '滞胀',
        'Regime_4': '衰退'
    }

    def __init__(
        self,
        n_regimes: int = 4,
        switching_mean: bool = True,
        switching_var: bool = False
    ):
        super().__init__(n_regimes, switching_mean, switching_var)

    def fit_with_factors(
        self,
        growth_factor: pd.Series,
        inflation_factor: pd.Series,
        liquidity_factor: Optional[pd.Series] = None,
        target_variable: Optional[pd.Series] = None
    ) -> 'MacroRegimeModel':
        """
        使用因子拟合宏观区制模型

        Parameters
        ----------
        growth_factor : pd.Series
            经济增长因子
        inflation_factor : pd.Series
            通胀因子
        liquidity_factor : pd.Series, optional
            流动性因子
        target_variable : pd.Series, optional
            目标变量（如GDP增长率），如果为None则使用增长因子

        Returns
        -------
        self
        """
        # 选择目标变量
        if target_variable is None:
            target_variable = growth_factor

        # 拟合模型
        self.fit(target_variable, method='statsmodels')

        # 保存因子
        self.growth_factor = growth_factor
        self.inflation_factor = inflation_factor
        if liquidity_factor is not None:
            self.liquidity_factor = liquidity_factor

        return self

    def interpret_regimes(self) -> Dict[str, Dict]:
        """
        解释各区制的经济含义

        基于因子特征进行解释

        Returns
        -------
        interpretation : dict
            区制解释
        """
        if not hasattr(self, 'growth_factor'):
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

            interpretation[regime] = {
                'economic_meaning': self.REGIME_NAMES.get(regime, regime),
                'growth_factor_mean': growth_mean,
                'inflation_factor_mean': inflation_mean,
                'description': self._get_regime_description(growth_mean, inflation_mean)
            }

        return interpretation

    def _get_regime_description(self, growth: float, inflation: float) -> str:
        """
        根据因子均值生成区制描述
        """
        if growth > 0 and inflation < 0:
            return "复苏：经济增长上升，通胀温和"
        elif growth > 0 and inflation > 0:
            return "过热：经济增长强劲，通胀压力较大"
        elif growth < 0 and inflation > 0:
            return "滞胀：经济疲弱，通胀高企"
        elif growth < 0 and inflation < 0:
            return "衰退：经济收缩，通胀下行"
        else:
            return "过渡期"


def test_markov_switching():
    """
    测试马尔可夫区制转移模型
    """
    print("=" * 60)
    print("测试马尔可夫区制转移模型")
    print("=" * 60)

    # 生成模拟数据
    np.random.seed(42)

    # 生成4个区制的模拟数据
    n_obs = 200
    true_regimes = []
    data = []

    regime_means = [-2, 3, 0, -3]  # 复苏、过热、滞胀、衰退
    regime_stds = [1, 1.5, 1.2, 2]

    for i in range(n_obs):
        if i < 50:
            regime = 0
        elif i < 100:
            regime = 1
        elif i < 150:
            regime = 2
        else:
            regime = 3

        true_regimes.append(regime)
        data.append(np.random.normal(regime_means[regime], regime_stds[regime]))

    # 转为Series
    index = pd.date_range('2010-01-01', periods=n_obs, freq='M')
    data_series = pd.Series(data, index=index)

    # 拟合模型
    print("\n[1] 拟合马尔可夫转移模型...")
    ms_model = MacroRegimeModel(n_regimes=4)
    ms_model.fit(data_series, method='hmmlearn')

    # 获取区制概率
    print("\n[2] 获取区制概率...")
    regime_probs = ms_model.get_regime_probs()
    print(f"区制概率（最后5期）：")
    print(regime_probs.tail())

    # 获取转移概率矩阵
    print("\n[3] 获取转移概率矩阵...")
    transition = ms_model.get_transition_matrix()
    print(transition)

    # 获取区制持续期
    print("\n[4] 获取区制期望持续期...")
    durations = ms_model.get_regime_durations()
    for regime, duration in durations.items():
        print(f"{regime}: {duration:.2f} 期")

    # 预测下一期
    print("\n[5] 预测下一期区制...")
    next_regime, next_prob = ms_model.predict_next_regime()
    print(f"下一期最可能区制：{next_regime}，概率：{next_prob:.2%}")

    # 绘图
    print("\n[6] 绘制区制概率...")
    fig1 = ms_model.plot_regime_probs(figsize=(14, 8))
    fig1.savefig('models/regime/regime_probs_plot.png', dpi=100, bbox_inches='tight')

    print("\n[7] 绘制区制序列...")
    fig2 = ms_model.plot_regime_sequence(data_series, figsize=(14, 6))
    fig2.savefig('models/regime/regime_sequence_plot.png', dpi=100, bbox_inches='tight')

    print("\n图表已保存！")

    return ms_model


if __name__ == '__main__':
    # 运行测试
    ms_model = test_markov_switching()
