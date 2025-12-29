"""
美国宏观经济周期识别模型

基于马尔可夫区制转移模型识别美国宏观状态：
1. 复苏（Recovery）
2. 过热（Overheat）
3. 滞胀（Stagflation）
4. 衰退（Recession）
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.regime.markov_switching import MacroRegimeModel
from models.dfm.us_dfm import USDFM


class USRegimeModel(MacroRegimeModel):
    """
    美国宏观状态识别模型

    输入：
    - 经济增长因子
    - 通胀因子
    - 流动性因子

    输出：
    - 每日的宏观状态概率
    - 最可能的宏观状态
    """

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
        super().__init__(n_regimes=n_regimes)

        # 加载美国DFM模型
        self.dfm_model = USDFM(n_factors=3)

    def load_data_and_fit(
        self,
        csv_path: str = 'data/processed/us/all_indicators.csv',
        start_date: str = '2010-01-01',
        method: str = 'pca'
    ) -> 'USRegimeModel':
        """
        加载数据并拟合模型

        Parameters
        ----------
        csv_path : str
            CSV文件路径
        start_date : str
            开始日期
        method : str
            DFM估计方法

        Returns
        -------
        self
        """
        print("=" * 60)
        print("美国宏观状态识别模型")
        print("=" * 60)

        # [1] 加载宏观数据
        print("\n[1] 加载美国宏观数据...")
        macro_data = self.dfm_model.fetch_from_csv(csv_path, start_date=start_date)

        # [2] 提取因子
        print("\n[2] 提取动态因子...")
        self.dfm_model.fit(macro_data, method=method)
        factors = self.dfm_model.get_factors()

        print(f"成功提取 {len(factors.columns)} 个因子，{len(factors)} 个时间点")

        # [3] 使用因子拟合区制模型
        print("\n[3] 拟合马尔可夫区制转移模型...")
        self.fit_with_factors(
            growth_factor=factors.iloc[:, 0],  # 经济增长因子
            inflation_factor=factors.iloc[:, 1],  # 通胀因子
            liquidity_factor=factors.iloc[:, 2]  # 流动性因子
        )

        # [4] 解释区制
        print("\n[4] 解释各区制经济含义...")
        interpretation = self.interpret_regimes()
        for regime, info in interpretation.items():
            print(f"\n{regime}: {info['economic_meaning']}")
            print(f"  描述：{info['description']}")
            print(f"  增长因子均值：{info['growth_factor_mean']:.2f}")
            print(f"  通胀因子均值：{info['inflation_factor_mean']:.2f}")

        # [5] 获取转移概率矩阵
        print("\n[5] 状态转移概率矩阵：")
        transition = self.get_transition_matrix()
        print(transition)

        # [6] 获取区制持续期
        print("\n[6] 各区制期望持续期（月）：")
        durations = self.get_regime_durations()
        for regime, duration in durations.items():
            print(f"  {regime}: {duration:.2f} 个月")

        return self

    def validate_with_nber(self) -> Dict[str, float]:
        """
        使用NBER衰退期验证模型准确性

        Returns
        -------
        metrics : dict
            验证指标
        """
        print("\n[验证] 与NBER衰退期对比...")

        results = {}

        for recession_name, (start, end) in self.NBER_RECESSIONS.items():
            # 找出模型识别的衰退期
            recession_periods = self.regime_sequence == 'Regime_4'  # 假设Regime_4是衰退

            # 检查NBER衰退期是否被识别
            nber_recession_dates = pd.date_range(start, end, freq='M')
            identified = sum(recession_periods.loc[nber_recession_dates])
            total = len(nber_recession_dates)
            accuracy = identified / total if total > 0 else 0

            results[recession_name] = {
                'nber_dates': (start, end),
                'identified_periods': identified,
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


def test_us_regime_model():
    """
    测试美国区制模型
    """
    # 创建模型
    us_regime = USRegimeModel(n_regimes=4)

    # 加载数据并拟合
    us_regime.load_data_and_fit(
        csv_path='data/processed/us/all_indicators.csv',
        start_date='2010-01-01'
    )

    # 验证
    us_regime.validate_with_nber()

    # 获取当前状态
    print("\n[当前状态]")
    current = us_regime.get_current_regime()
    print(f"日期：{current['date']}")
    print(f"区制：{current['regime']} - {current['regime_name']}")
    print(f"描述：{current['description']}")
    print(f"各区制概率：{current['regime_probs']}")

    # 预测下一期
    print("\n[预测]")
    next_regime, next_prob = us_regime.predict_next_regime()
    print(f"下一期最可能区制：{next_regime}，概率：{next_prob:.2%}")

    # 导出数据
    us_regime.export_regime_data()

    # 绘图
    print("\n[绘图]")
    import matplotlib.pyplot as plt

    fig1 = us_regime.plot_regime_probs(figsize=(14, 8))
    fig1.savefig('models/regime/us_regime_probs_plot.png', dpi=100, bbox_inches='tight')
    print("区制概率图已保存")

    # 绘制区制序列
    fig2 = us_regime.plot_regime_sequence(
        us_regime.growth_factor,
        figsize=(14, 6)
    )
    fig2.savefig('models/regime/us_regime_sequence_plot.png', dpi=100, bbox_inches='tight')
    print("区制序列图已保存")

    return us_regime


if __name__ == '__main__':
    # 运行测试
    test_us_regime_model()
