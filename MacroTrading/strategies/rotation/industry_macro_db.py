"""
宏观状态-行业表现数据库

建立不同宏观状态下的行业表现特征，为行业轮动提供数据支持

功能：
1. 记录各行业在不同宏观状态下的历史表现
2. 计算行业表现统计指标
3. 建立宏观状态-行业映射关系
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class IndustryMacroDB:
    """
    宏观状态-行业表现数据库

    存储和分析各行业在不同宏观状态下的表现
    """

    def __init__(self):
        """初始化数据库"""
        self.industry_data = {}  # 行业数据
        self.regime_mapping = {}  # 区制映射
        self.performance_stats = {}  # 表现统计

        # 宏观状态定义
        self.regimes = {
            'Regime_1': '正常增长',
            'Regime_2': '过热',
            'Regime_3': '衰退',
            'Regime_4': '滞胀'
        }

    def load_industry_data(
        self,
        industry_prices: Dict[str, pd.DataFrame],
        regime_sequence: pd.Series
    ):
        """
        加载行业价格数据和区制序列

        Parameters:
        -----------
        industry_prices : dict
            行业价格数据，例如：{'金融': df, '科技': df, ...}
            DataFrame包含列：date, close
        regime_sequence : Series
            区制序列，索引为日期，值为区制名称
        """
        # 保存区制序列
        self.regime_sequence = regime_sequence

        # 处理每个行业数据
        for industry_name, price_df in industry_prices.items():
            # 转换日期格式
            price_df['date'] = pd.to_datetime(price_df['date'])
            price_df.set_index('date', inplace=True)

            # 计算收益率
            price_df['returns'] = price_df['close'].pct_change()

            # 合并区制信息
            merged = price_df.join(regime_sequence, how='left')

            # 填充缺失的区制（前向填充）
            merged['regime'].fillna(method='ffill', inplace=True)

            # 保存
            self.industry_data[industry_name] = merged

        print(f"已加载 {len(industry_prices)} 个行业的数据")

    def calculate_regime_performance(
        self,
        holding_period: int = 20
    ) -> pd.DataFrame:
        """
        计算各行业在不同区制下的表现

        Parameters:
        -----------
        holding_period : int
            持有周期（默认20个交易日）

        Returns:
        --------
        DataFrame
            各行业在各区制下的表现统计
        """
        performance_data = []

        for industry_name, data in self.industry_data.items():
            for regime in self.regimes.keys():
                # 筛选该区制时期的数据
                regime_data = data[data['regime'] == regime]

                if len(regime_data) < holding_period:
                    continue

                # 计算累计收益率
                regime_data['cum_returns'] = (1 + regime_data['returns']).cumprod()

                # 计算持有期收益（滚动）
                rolling_returns = regime_data['cum_returns'].pct_change(holding_period)

                # 统计指标
                stats = {
                    'industry': industry_name,
                    'regime': regime,
                    'mean_return': rolling_returns.mean(),
                    'median_return': rolling_returns.median(),
                    'std_return': rolling_returns.std(),
                    'win_rate': (rolling_returns > 0).sum() / len(rolling_returns),
                    'max_return': rolling_returns.max(),
                    'min_return': rolling_returns.min(),
                    'sharpe_ratio': rolling_returns.mean() / rolling_returns.std() if rolling_returns.std() > 0 else 0,
                    'n_observations': len(rolling_returns)
                }

                performance_data.append(stats)

        # 转换为DataFrame
        df_performance = pd.DataFrame(performance_data)

        # 保存
        self.performance_stats = df_performance

        return df_performance

    def get_regime_ranking(
        self,
        regime: str,
        metric: str = 'mean_return',
        top_n: int = 5
    ) -> pd.DataFrame:
        """
        获取指定区制下的行业排名

        Parameters:
        -----------
        regime : str
            区制名称（Regime_1, Regime_2, ...）
        metric : str
            排序指标（mean_return, sharpe_ratio, win_rate等）
        top_n : int
            返回前N个行业

        Returns:
        --------
        DataFrame
            行业排名
        """
        if self.performance_stats is None or self.performance_stats.empty:
            raise ValueError("请先调用 calculate_regime_performance()")

        # 筛选指定区制
        regime_data = self.performance_stats[
            self.performance_stats['regime'] == regime
        ].copy()

        # 排序
        regime_data = regime_data.sort_values(by=metric, ascending=False)

        # 返回前N个
        return regime_data.head(top_n)

    def get_industry_allocation(
        self,
        current_regime: str,
        method: str = 'top_n',
        top_n: int = 3,
        min_weight: float = 0.10,
        max_weight: float = 0.40
    ) -> Dict[str, float]:
        """
        根据当前区制生成行业配置建议

        Parameters:
        -----------
        current_regime : str
            当前区制
        method : str
            配置方法：'top_n', 'weighted', 'equal'
        top_n : int
            选择前N个行业
        min_weight : float
            最小权重
        max_weight : float
            最大权重

        Returns:
        --------
        dict
            行业权重，例如：{'金融': 0.35, '科技': 0.35, '消费': 0.30}
        """
        if self.performance_stats is None or self.performance_stats.empty:
            raise ValueError("请先调用 calculate_regime_performance()")

        # 获取当前区制下的行业排名
        ranking = self.get_regime_ranking(current_regime, top_n=top_n * 2)

        if method == 'top_n':
            # 选择前N个行业，等权配置
            selected = ranking.head(top_n)
            weight = 1.0 / len(selected)
            allocation = {row['industry']: weight for _, row in selected.iterrows()}

        elif method == 'weighted':
            # 根据夏普比率加权
            selected = ranking.head(top_n)
            sharpe_ratios = selected['sharpe_ratio'].values
            sharpe_ratios[sharpe_ratios < 0] = 0  # 负夏普设为0

            # 归一化
            weights = sharpe_ratios / sharpe_ratios.sum()

            # 限制权重范围
            weights = np.clip(weights, min_weight, max_weight)
            weights = weights / weights.sum()  # 重新归一化

            allocation = {
                row['industry']: weights[i]
                for i, (_, row) in enumerate(selected.iterrows())
            }

        elif method == 'equal':
            # 等权配置
            selected = ranking.head(top_n)
            weight = 1.0 / len(selected)
            allocation = {row['industry']: weight for _, row in selected.iterrows()}

        else:
            raise ValueError(f"未知的配置方法: {method}")

        return allocation

    def get_regime_transition_allocation(
        self,
        from_regime: str,
        to_regime: str,
        transition_days: int = 5
    ) -> Dict[str, float]:
        """
        获取区制转换期间的行业配置建议

        Parameters:
        -----------
        from_regime : str
            原区制
        to_regime : str
            新区制
        transition_days : int
            转换天数

        Returns:
        --------
        dict
            转换期行业权重
        """
        # 获取两个区制的配置
        allocation_from = self.get_industry_allocation(from_regime, method='weighted', top_n=3)
        allocation_to = self.get_industry_allocation(to_regime, method='weighted', top_n=3)

        # 合并行业集合
        all_industries = set(allocation_from.keys()) | set(allocation_to.keys())

        # 线性插值
        transition_allocation = {}
        for industry in all_industries:
            weight_from = allocation_from.get(industry, 0.0)
            weight_to = allocation_to.get(industry, 0.0)

            # 在转换期内逐渐调整
            # 这里简化为取平均
            transition_allocation[industry] = (weight_from + weight_to) / 2

        # 归一化
        total = sum(transition_allocation.values())
        if total > 0:
            transition_allocation = {k: v/total for k, v in transition_allocation.items()}

        return transition_allocation

    def export_to_csv(self, output_dir: str = 'data/derived/industry/'):
        """
        导出数据到CSV

        Parameters:
        -----------
        output_dir : str
            输出目录
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        # 导出表现统计
        if self.performance_stats is not None:
            self.performance_stats.to_csv(
                f'{output_dir}/industry_regime_performance.csv',
                index=False,
                encoding='utf-8-sig'
            )
            print(f"已导出: {output_dir}/industry_regime_performance.csv")

        # 导出区制序列
        if self.regime_sequence is not None:
            self.regime_sequence.to_csv(
                f'{output_dir}/regime_sequence.csv',
                encoding='utf-8-sig'
            )
            print(f"已导出: {output_dir}/regime_sequence.csv")

    def generate_summary_report(self) -> str:
        """
        生成摘要报告

        Returns:
        --------
        str
            报告内容
        """
        if self.performance_stats is None or self.performance_stats.empty:
            return "暂无数据，请先加载数据并计算表现"

        report = []
        report.append("=" * 80)
        report.append("宏观状态-行业表现数据库摘要")
        report.append("=" * 80)
        report.append("")

        # 各区制下的最佳行业
        for regime in self.regimes.keys():
            report.append(f"{self.regimes[regime]} ({regime})")
            report.append("-" * 80)

            try:
                top_industries = self.get_regime_ranking(regime, top_n=3)

                for _, row in top_industries.iterrows():
                    report.append(
                        f"  {row['industry']}: "
                        f"平均收益={row['mean_return']:.2%}, "
                        f"夏普比率={row['sharpe_ratio']:.2f}, "
                        f"胜率={row['win_rate']:.2%}"
                    )
            except:
                report.append("  数据不足")

            report.append("")

        report.append("=" * 80)

        return "\n".join(report)


# 便捷函数
def create_industry_macro_db(
    industry_prices: Dict[str, pd.DataFrame],
    regime_sequence: pd.Series
) -> IndustryMacroDB:
    """
    便捷函数：创建行业-宏观数据库

    Parameters:
    -----------
    industry_prices : dict
        行业价格数据
    regime_sequence : Series
        区制序列

    Returns:
    --------
    IndustryMacroDB
        数据库对象
    """
    db = IndustryMacroDB()
    db.load_industry_data(industry_prices, regime_sequence)
    db.calculate_regime_performance()

    return db
