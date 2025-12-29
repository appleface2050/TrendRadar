"""
滚动窗口动态因子模型

目的：
1. 避免结构性断裂（structural break）
2. 捕捉时变参数
3. 提高模型的样本外预测能力

核心思想：
- 使用固定长度窗口（如5年数据）估计DFM
- 每次滚动一个时间单位（如1个月）
- 重新估计模型参数
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import warnings

from models.dfm.us_dfm import USDFM
from models.dfm.cn_dfm import CNDFM

warnings.filterwarnings('ignore')


class RollingDFM:
    """
    滚动窗口动态因子模型

    适用于：
    - 检验因子稳定性
    - 避免结构性断裂
    - 提高样本外预测能力
    """

    def __init__(
        self,
        base_model: Union[USDFM, CNDFM],
        window_size: int = 60,  # 5年月度数据
        step_size: int = 1,      # 每次滚动1个时间单位
        min_obs: int = 30        # 最小观测值数
    ):
        """
        初始化滚动DFM

        Parameters
        ----------
        base_model : USDFM or CNDFM
            基础DFM模型
        window_size : int
            窗口大小（时间点数）
        step_size : int
            滚动步长
        min_obs : int
            每个窗口的最小观测值数
        """
        self.base_model = base_model
        self.window_size = window_size
        self.step_size = step_size
        self.min_obs = min_obs

        # 存储结果
        self.rolling_factors = []
        self.rolling_loadings = []
        self.windows = []

    def fit(
        self,
        data: pd.DataFrame,
        method: str = 'pca'
    ) -> 'RollingDFM':
        """
        滚动估计DFM

        Parameters
        ----------
        data : pd.DataFrame
            数据（索引为日期）
        method : str
            估计方法

        Returns
        -------
        self
        """
        print(f"开始滚动估计DFM...")
        print(f"数据范围：{data.index.min()} 至 {data.index.max()}（共{len(data)}个时间点）")
        print(f"窗口大小：{self.window_size}, 步长：{self.step_size}")

        # 确保数据有足够的观测值
        if len(data) < self.window_size:
            raise ValueError(f"数据量不足：需要至少{self.window_size}个观测值，实际只有{len(data)}个")

        # 生成滚动窗口
        n_windows = (len(data) - self.window_size) // self.step_size + 1
        print(f"将估计 {n_windows} 个窗口...\n")

        for i in range(n_windows):
            start_idx = i * self.step_size
            end_idx = start_idx + self.window_size

            # 提取窗口数据
            window_data = data.iloc[start_idx:end_idx]

            # 检查数据质量
            if window_data.isnull().sum().sum() / window_data.size > 0.3:
                print(f"窗口 {i+1}/{n_windows}（{window_data.index.min().date()} 至 {window_data.index.max().date()}）：缺失率过高，跳过")
                continue

            # 移除含无穷值的列
            window_data = window_data.replace([np.inf, -np.inf], np.nan)
            window_data = window_data.dropna()

            if len(window_data) < self.min_obs:
                print(f"窗口 {i+1}/{n_windows}：有效数据不足，跳过")
                continue

            try:
                # 复制基础模型
                model = type(self.base_model)(
                    n_factors=self.base_model.n_factors,
                    factor_orders=self.base_model.factor_orders,
                    standardize=self.base_model.standardize
                )

                # 拟合模型
                model.fit(window_data, method=method)

                # 保存结果
                factors = model.get_factors()
                loadings = model.get_factor_loadings()

                # 只保留最后一个时间点的因子（避免重复）
                self.rolling_factors.append(factors.iloc[-1])
                self.rolling_loadings.append(loadings)
                self.windows.append({
                    'start': window_data.index.min(),
                    'end': window_data.index.max(),
                    'n_obs': len(window_data)
                })

                print(f"窗口 {i+1}/{n_windows}（{window_data.index.min().date()} 至 {window_data.index.max().date()}）：成功")

            except Exception as e:
                print(f"窗口 {i+1}/{n_windows}：估计失败 - {e}")
                continue

        # 合并结果
        if self.rolling_factors:
            self.rolling_factors = pd.DataFrame(self.rolling_factors)
            print(f"\n滚动估计完成！共 {len(self.rolling_factors)} 个有效窗口")
        else:
            raise ValueError("滚动估计失败：没有有效窗口")

        return self

    def get_rolling_factors(self) -> pd.DataFrame:
        """
        获取滚动因子序列

        Returns
        -------
        pd.DataFrame
            因子序列
        """
        if not self.rolling_factors:
            raise ValueError("模型尚未拟合，请先调用fit()方法")
        return self.rolling_factors

    def get_factor_stability(
        self,
        window: int = 12
    ) -> pd.DataFrame:
        """
        计算因子稳定性（滚动相关系数）

        Parameters
        ----------
        window : int
            滚动窗口大小

        Returns
        -------
        pd.DataFrame
            滚动相关系数
        """
        factors = self.get_rolling_factors()
        rolling_corr = factors.rolling(window=window).corr()
        return rolling_corr

    def detect_structural_breaks(
        self,
        threshold: float = 0.5
    ) -> List[Dict]:
        """
        检测结构性断裂点

        方法：检查因子载荷的突然变化

        Parameters
        ----------
        threshold : float
            载荷变化阈值

        Returns
        -------
        breaks : list
            断裂点列表
        """
        if len(self.rolling_loadings) < 2:
            return []

        breaks = []

        for i in range(1, len(self.rolling_loadings)):
            # 计算相邻窗口的载荷变化
            loading_prev = self.rolling_loadings[i-1]
            loading_curr = self.rolling_loadings[i]

            # 确保是DataFrame格式
            if isinstance(loading_prev, pd.DataFrame):
                loading_prev = loading_prev.values
            if isinstance(loading_curr, pd.DataFrame):
                loading_curr = loading_curr.values

            # 计算变化幅度
            delta = np.abs(loading_curr - loading_prev).mean()

            if delta > threshold:
                breaks.append({
                    'window': i,
                    'date': self.windows[i]['end'],
                    'delta': delta
                })

        return breaks

    def plot_rolling_factors(
        self,
        figsize: Tuple[int, int] = (14, 8)
    ):
        """
        绘制滚动因子

        Parameters
        ----------
        figsize : tuple
            图形大小
        """
        import matplotlib.pyplot as plt

        factors = self.get_rolling_factors()

        fig, axes = plt.subplots(
            factors.shape[1],
            1,
            figsize=figsize,
            sharex=True
        )

        if factors.shape[1] == 1:
            axes = [axes]

        for i, ax in enumerate(axes):
            factor_name = factors.columns[i]
            ax.plot(factors.index, factors.iloc[:, i])
            ax.set_title(f'滚动{factor_name}')
            ax.grid(True, alpha=0.3)

            # 标注结构性断裂点（如果检测到）
            breaks = self.detect_structural_breaks()
            if breaks:
                for break_info in breaks:
                    if break_info['date'] in factors.index:
                        ax.axvline(
                            break_info['date'],
                            color='red',
                            linestyle='--',
                            alpha=0.5
                        )

        plt.tight_layout()
        return fig

    def compare_full_vs_rolling(
        self,
        full_model_factors: pd.DataFrame
    ) -> pd.DataFrame:
        """
        比较全样本和滚动窗口的因子差异

        Parameters
        ----------
        full_model_factors : pd.DataFrame
            全样本模型估计的因子

        Returns
        -------
        pd.DataFrame
            相关性矩阵
        """
        rolling_factors = self.get_rolling_factors()

        # 对齐时间索引
        common_index = full_model_factors.index.intersection(rolling_factors.index)

        full_aligned = full_model_factors.loc[common_index]
        rolling_aligned = rolling_factors.loc[common_index]

        # 计算相关性
        comparison = pd.DataFrame(index=full_aligned.columns)

        for factor in full_aligned.columns:
            if factor in rolling_aligned.columns:
                corr = full_aligned[factor].corr(rolling_aligned[factor])
                comparison.loc[factor, 'correlation'] = corr

        return comparison


class ExpandingWindowDFM(RollingDFM):
    """
    扩展窗口DFM（每次增加新数据，不删除旧数据）

    优点：充分利用所有历史数据
    缺点：可能受结构性断裂影响
    """

    def __init__(
        self,
        base_model: Union[USDFM, CNDFM],
        min_window: int = 30,
        step_size: int = 1
    ):
        """
        参数
        ----
        min_window : int
            最小窗口大小
        step_size : int
            扩展步长
        """
        super().__init__(
            base_model=base_model,
            window_size=None,  # 扩展窗口不限制大小
            step_size=step_size,
            min_obs=min_window
        )
        self.min_window = min_window

    def fit(
        self,
        data: pd.DataFrame,
        method: str = 'pca'
    ) -> 'ExpandingWindowDFM':
        """
        使用扩展窗口估计DFM

        Parameters
        ----------
        data : pd.DataFrame
            数据
        method : str
            估计方法

        Returns
        -------
        self
        """
        print(f"开始扩展窗口估计DFM...")
        print(f"数据范围：{data.index.min()} 至 {data.index.max()}（共{len(data)}个时间点）")
        print(f"最小窗口：{self.min_window}, 步长：{self.step_size}")

        # 扩展窗口估计
        n_windows = (len(data) - self.min_window) // self.step_size + 1
        print(f"将估计 {n_windows} 个窗口...\n")

        for i in range(n_windows):
            end_idx = self.min_window + i * self.step_size

            # 提取扩展窗口数据
            window_data = data.iloc[:end_idx]

            # 检查数据质量
            if window_data.isnull().sum().sum() / window_data.size > 0.3:
                print(f"窗口 {i+1}/{n_windows}（截至{window_data.index.max().date()}）：缺失率过高，跳过")
                continue

            # 移除含无穷值的列
            window_data = window_data.replace([np.inf, -np.inf], np.nan)
            window_data = window_data.dropna()

            if len(window_data) < self.min_window:
                print(f"窗口 {i+1}/{n_windows}：有效数据不足，跳过")
                continue

            try:
                # 复制基础模型
                model = type(self.base_model)(
                    n_factors=self.base_model.n_factors,
                    factor_orders=self.base_model.factor_orders,
                    standardize=self.base_model.standardize
                )

                # 拟合模型
                model.fit(window_data, method=method)

                # 保存结果（只保留最后一个时间点）
                factors = model.get_factors()
                loadings = model.get_factor_loadings()

                self.rolling_factors.append(factors.iloc[-1])
                self.rolling_loadings.append(loadings)
                self.windows.append({
                    'start': window_data.index.min(),
                    'end': window_data.index.max(),
                    'n_obs': len(window_data)
                })

                print(f"窗口 {i+1}/{n_windows}（{window_data.index.min().date()} 至 {window_data.index.max().date()}）：成功")

            except Exception as e:
                print(f"窗口 {i+1}/{n_windows}：估计失败 - {e}")
                continue

        # 合并结果
        if self.rolling_factors:
            self.rolling_factors = pd.DataFrame(self.rolling_factors)
            print(f"\n扩展窗口估计完成！共 {len(self.rolling_factors)} 个有效窗口")
        else:
            raise ValueError("估计失败：没有有效窗口")

        return self


def test_rolling_dfm():
    """
    测试滚动DFM
    """
    print("=" * 60)
    print("测试滚动窗口动态因子模型")
    print("=" * 60)

    # 准备数据
    print("\n[1] 加载美国宏观数据...")
    from models.dfm.us_dfm import USDFM

    us_dfm = USDFM(n_factors=3)
    data = us_dfm.fetch_from_csv(
        csv_path='data/processed/us/all_indicators.csv',
        start_date='2010-01-01'
    )

    # 创建滚动DFM
    print("\n[2] 创建滚动DFM模型...")
    rolling_dfm = RollingDFM(
        base_model=us_dfm,
        window_size=60,   # 5年月度数据
        step_size=1,      # 每月滚动
        min_obs=30
    )

    # 拟合模型
    print("\n[3] 滚动估计DFM...")
    rolling_dfm.fit(data, method='pca')

    # 获取因子
    print("\n[4] 获取滚动因子...")
    rolling_factors = rolling_dfm.get_rolling_factors()
    print(f"因子统计摘要：")
    print(rolling_factors.describe())

    # 检验稳定性
    print("\n[5] 检验因子稳定性...")
    stability = rolling_dfm.get_factor_stability(window=12)
    print(f"因子间滚动相关系数（最后时期）：")
    print(stability.iloc[-1])

    # 检测结构性断裂
    print("\n[6] 检测结构性断裂...")
    breaks = rolling_dfm.detect_structural_breaks(threshold=0.3)
    if breaks:
        print(f"检测到 {len(breaks)} 个结构性断裂点：")
        for break_info in breaks:
            print(f"  - {break_info['date'].date()}: delta={break_info['delta']:.4f}")
    else:
        print("未检测到明显的结构性断裂")

    # 绘图
    print("\n[7] 绘制滚动因子...")
    fig = rolling_dfm.plot_rolling_factors(figsize=(14, 8))
    fig.savefig('models/dfm/rolling_factors_plot.png', dpi=100, bbox_inches='tight')
    print("图表已保存到：models/dfm/rolling_factors_plot.png")

    return rolling_dfm


if __name__ == '__main__':
    # 运行测试
    rolling_dfm = test_rolling_dfm()
