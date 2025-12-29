"""
绩效归因分析

分析宏观策略的收益来源

功能：
1. 收益分解
2. 因子贡献度分析
3. 择时能力评估
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class PerformanceAttribution:
    """
    绩效归因分析器

    分析策略收益来源
    """

    def __init__(self):
        """初始化"""
        self.attribution_results = None

    def analyze_attribution(
        self,
        strategy_returns: pd.Series,
        benchmark_returns: pd.Series,
        factor_returns: pd.DataFrame,
        macro_scores: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        分析绩效归因

        Parameters:
        -----------
        strategy_returns : Series
            策略收益率
        benchmark_returns : Series
            基准收益率
        factor_returns : DataFrame
            因子收益率（包含各宏观因子的收益贡献）
        macro_scores : DataFrame, optional
            宏观得分

        Returns:
        --------
        dict
            归因分析结果
        """
        # 对齐数据
        common_index = strategy_returns.index.intersection(benchmark_returns.index)
        strategy_returns = strategy_returns.loc[common_index]
        benchmark_returns = benchmark_returns.loc[common_index]

        # 1. 总收益分解
        total_return = (1 + strategy_returns).prod() - 1
        benchmark_return = (1 + benchmark_returns).prod() - 1
        excess_return = total_return - benchmark_return

        # 2. 资产配置效应（简化）
        allocation_effect = self._calculate_allocation_effect(
            strategy_returns, benchmark_returns
        )

        # 3. 择时效应
        timing_effect = self._calculate_timing_effect(
            strategy_returns, benchmark_returns
        )

        # 4. 因子贡献度（如果提供因子收益）
        factor_contribution = None
        if factor_returns is not None and not factor_returns.empty:
            factor_contribution = self._calculate_factor_contribution(
                strategy_returns, factor_returns
            )

        # 5. 风险调整收益
        risk_adjusted_return = self._calculate_risk_adjusted_return(
            strategy_returns
        )

        results = {
            'total_return': total_return,
            'benchmark_return': benchmark_return,
            'excess_return': excess_return,
            'allocation_effect': allocation_effect,
            'timing_effect': timing_effect,
            'factor_contribution': factor_contribution,
            'risk_adjusted_return': risk_adjusted_return
        }

        self.attribution_results = results
        return results

    def _calculate_allocation_effect(
        self,
        strategy_returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> Dict:
        """
        计算资产配置效应
        """
        # 超额收益
        excess_returns = strategy_returns - benchmark_returns

        # 正收益天数和负收益天数
        positive_days = (excess_returns > 0).sum()
        negative_days = (excess_returns < 0).sum()

        # 平均超额收益
        avg_excess = excess_returns.mean()

        # 配置效应（简化计算）
        allocation_effect = {
            'avg_excess_return': avg_excess,
            'positive_days': positive_days,
            'negative_days': negative_days,
            'win_rate': positive_days / (positive_days + negative_days) if (positive_days + negative_days) > 0 else 0
        }

        return allocation_effect

    def _calculate_timing_effect(
        self,
        strategy_returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> Dict:
        """
        计算择时效应
        """
        # 计算相关系数
        correlation = strategy_returns.corr(benchmark_returns)

        # 上行捕获率
        up_periods = benchmark_returns > 0
        if up_periods.sum() > 0:
            up_capture = (
                strategy_returns[up_periods].mean() /
                benchmark_returns[up_periods].mean()
                if benchmark_returns[up_periods].mean() != 0 else 0
            )
        else:
            up_capture = 0

        # 下行捕获率
        down_periods = benchmark_returns < 0
        if down_periods.sum() > 0:
            down_capture = (
                strategy_returns[down_periods].mean() /
                benchmark_returns[down_periods].mean()
                if benchmark_returns[down_periods].mean() != 0 else 0
            )
        else:
            down_capture = 0

        timing_effect = {
            'correlation': correlation,
            'up_capture': up_capture,
            'down_capture': down_capture
        }

        return timing_effect

    def _calculate_factor_contribution(
        self,
        strategy_returns: pd.Series,
        factor_returns: pd.DataFrame
    ) -> Dict:
        """
        计算因子贡献度
        """
        # 对齐索引
        common_index = strategy_returns.index.intersection(factor_returns.index)
        strategy_returns = strategy_returns.loc[common_index]
        factor_returns = factor_returns.loc[common_index]

        # 计算每个因子的贡献（简单线性回归）
        contributions = {}

        for factor in factor_returns.columns:
            factor_data = factor_returns[factor].dropna()
            if len(factor_data) > 0:
                # 计算相关系数作为贡献度
                corr = strategy_returns.corr(factor_data)
                contributions[factor] = {
                    'correlation': corr,
                    'avg_return': factor_data.mean(),
                    'std_return': factor_data.std()
                }

        return contributions

    def _calculate_risk_adjusted_return(
        self,
        returns: pd.Series
    ) -> Dict:
        """
        计算风险调整收益
        """
        # 年化收益率
        annual_return = returns.mean() * 252

        # 波动率
        annual_vol = returns.std() * np.sqrt(252)

        # 夏普比率（假设无风险利率为0）
        sharpe = annual_return / annual_vol if annual_vol > 0 else 0

        # 索提诺比率（下行风险）
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino = annual_return / downside_vol if downside_vol > 0 else 0

        # 最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # 卡玛比率
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        risk_adjusted = {
            'annual_return': annual_return,
            'annual_volatility': annual_vol,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar
        }

        return risk_adjusted

    def generate_attribution_report(self) -> str:
        """
        生成归因报告

        Returns:
        --------
        str
            报告内容
        """
        if self.attribution_results is None:
            return "尚未进行归因分析"

        results = self.attribution_results

        report = []
        report.append("=" * 80)
        report.append("绩效归因分析报告")
        report.append("=" * 80)
        report.append("")

        # 收益分解
        report.append("1. 收益分解")
        report.append("-" * 80)
        report.append(f"策略总收益: {results['total_return']:.2%}")
        report.append(f"基准收益: {results['benchmark_return']:.2%}")
        report.append(f"超额收益: {results['excess_return']:.2%}")
        report.append("")

        # 资产配置效应
        allocation = results['allocation_effect']
        report.append("2. 资产配置效应")
        report.append("-" * 80)
        report.append(f"平均超额收益: {allocation['avg_excess_return']:.4%}")
        report.append(f"正收益天数: {allocation['positive_days']}")
        report.append(f"负收益天数: {allocation['negative_days']}")
        report.append(f"胜率: {allocation['win_rate']:.2%}")
        report.append("")

        # 择时效应
        timing = results['timing_effect']
        report.append("3. 择时效应")
        report.append("-" * 80)
        report.append(f"与基准相关性: {timing['correlation']:.2f}")
        report.append(f"上行捕获率: {timing['up_capture']:.2f}")
        report.append(f"下行捕获率: {timing['down_capture']:.2f}")
        report.append("")

        # 风险调整收益
        risk_adj = results['risk_adjusted_return']
        report.append("4. 风险调整收益")
        report.append("-" * 80)
        report.append(f"年化收益: {risk_adj['annual_return']:.2%}")
        report.append(f"年化波动: {risk_adj['annual_volatility']:.2%}")
        report.append(f"夏普比率: {risk_adj['sharpe_ratio']:.2f}")
        report.append(f"索提诺比率: {risk_adj['sortino_ratio']:.2f}")
        report.append(f"最大回撤: {risk_adj['max_drawdown']:.2%}")
        report.append(f"卡玛比率: {risk_adj['calmar_ratio']:.2f}")
        report.append("")

        # 因子贡献（如果有）
        if results['factor_contribution'] is not None:
            report.append("5. 因子贡献度")
            report.append("-" * 80)
            for factor, metrics in results['factor_contribution'].items():
                report.append(
                    f"{factor}: 相关性={metrics['correlation']:.2f}, "
                    f"均收益={metrics['avg_return']:.4%}"
                )
            report.append("")

        report.append("=" * 80)

        return "\n".join(report)
