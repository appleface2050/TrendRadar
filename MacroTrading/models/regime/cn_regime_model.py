"""
中国宏观经济周期识别模型

基于马尔可夫区制转移模型识别中国宏观状态：
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
from models.dfm.cn_dfm import CNDFM


class CNRegimeModel(MacroRegimeModel):
    """
    中国宏观状态识别模型

    输入：
    - 经济增长因子
    - 通胀因子
    - 流动性因子

    输出：
    - 每日的宏观状态概率
    - 最可能的宏观状态
    """

    def __init__(self, n_regimes: int = 4):
        """
        初始化中国区制模型

        Parameters
        ----------
        n_regimes : int
            区制数量（默认4个）
        """
        super().__init__(n_regimes=n_regimes)

        # 加载中国DFM模型
        self.dfm_model = CNDFM(n_factors=3)

    def load_data_and_fit(
        self,
        data_source: str = 'tushare',
        start_date: str = '2010-01-01',
        method: str = 'pca'
    ) -> 'CNRegimeModel':
        """
        加载数据并拟合模型

        Parameters
        ----------
        data_source : str
            数据源（'tushare' 或 'csv'）
        start_date : str
            开始日期
        method : str
            DFM估计方法

        Returns
        -------
        self
        """
        print("=" * 60)
        print("中国宏观状态识别模型")
        print("=" * 60)

        # [1] 加载宏观数据
        print("\n[1] 加载中国宏观数据...")
        if data_source == 'tushare':
            macro_data = self.dfm_model.fetch_macro_data(start_date=start_date)
        elif data_source == 'csv':
            # 如果有CSV备选
            macro_data = pd.read_csv('data/processed/china/all_indicators.csv', index_col=0, parse_dates=True)
        else:
            raise ValueError(f"未知的数据源：{data_source}")

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


def test_cn_regime_model():
    """
    测试中国区制模型
    """
    # 创建模型
    cn_regime = CNRegimeModel(n_regimes=4)

    # 注意：需要先配置Tushare Token
    print("提示：中国区制模型需要Tushare数据")
    print("使用前请确保：")
    print("1. 已配置Tushare Token（confidential.json）")
    print("2. 已获取中国宏观数据并存储到数据库")

    # 如果有数据，取消注释以下代码：
    # cn_regime.load_data_and_fit(
    #     data_source='tushare',
    #     start_date='2010-01-01'
    # )

    return cn_regime


if __name__ == '__main__':
    # 运行测试
    test_cn_regime_model()
