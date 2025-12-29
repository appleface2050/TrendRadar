"""
回测引擎

基于Backtrader的宏观策略回测引擎

功能：
1. 加载数据
2. 运行回测
3. 绩效分析
4. 结果对比
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    import backtrader as bt
    BACKTRADER_AVAILABLE = True
except ImportError:
    BACKTRADER_AVAILABLE = False
    print("Warning: backtrader not installed")

try:
    import quantstats as qs
    QUANTSTATS_AVAILABLE = True
except ImportError:
    QUANTSTATS_AVAILABLE = False
    print("Warning: quantstats not installed")

from backtest.aligner.macro_data_feed import MacroDataFactory
from backtest.strategies.macro_strategy import MacroStrategy, BuyAndHoldStrategy


class BacktestEngine:
    """
    回测引擎

    封装Backtrader的回测流程
    """

    def __init__(
        self,
        initial_cash: float = 1000000.0,
        commission: float = 0.001,
        slippage: float = 0.001
    ):
        """
        初始化回测引擎

        Parameters:
        -----------
        initial_cash : float
            初始资金（默认1,000,000）
        commission : float
            佣金率（默认0.1%）
        slippage : float
            滑点（默认0.1%）
        """
        self.initial_cash = initial_cash
        self.commission = commission
        self.slippage = slippable = slippage

        # 数据工厂
        self.data_factory = MacroDataFactory(use_calendar_aligner=True)

        # 回测结果
        self.results = None
        self.strategies = {}

    def run_backtest(
        self,
        price_file: str,
        macro_file: Optional[str] = None,
        risk_file: Optional[str] = None,
        regime_file: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        strategy_params: Optional[Dict] = None
    ) -> Dict:
        """
        运行回测

        Parameters:
        -----------
        price_file : str
            价格数据文件
        macro_file : str, optional
            宏观数据文件
        risk_file : str, optional
            风险数据文件
        regime_file : str, optional
            区制数据文件
        start_date : str, optional
            开始日期
        end_date : str, optional
            结束日期
        strategy_params : dict, optional
            策略参数

        Returns:
        --------
        dict
            回测结果
        """
        if not BACKTRADER_AVAILABLE:
            raise ImportError("backtrader未安装，无法运行回测")

        # 创建Cerebro引擎
        cerebro = bt.Cerebro()

        # 设置初始资金
        cerebro.broker.setcash(self.initial_cash)

        # 设置佣金
        cerebro.broker.setcommission(commission=self.commission)

        # 加载数据
        data_feed = self.data_factory.create_data_feed(
            price_data=self.data_factory.load_price_data(price_file, start_date, end_date),
            macro_data=self.data_factory.load_macro_data(macro_file, start_date, end_date) if macro_file else None,
            risk_data=self.data_factory.load_macro_data(risk_file, start_date, end_date) if risk_file else None,
            regime_data=self.data_factory.load_macro_data(regime_file, start_date, end_date) if regime_file else None
        )

        cerebro.adddata(data_feed)

        # 添加策略
        if strategy_params:
            cerebro.addstrategy(MacroStrategy, **strategy_params)
        else:
            cerebro.addstrategy(MacroStrategy)

        # 添加分析器
        self._add_analyzers(cerebro)

        # 运行回测
        print("开始回测...")
        results = cerebro.run()
        strategy = results[0]

        # 保存结果
        self.results = {
            'strategy': strategy,
            'cerebro': cerebro,
            'initial_cash': self.initial_cash,
            'final_value': cerebro.broker.getvalue(),
            'metrics': strategy.get_performance_metrics()
        }

        # 添加基准策略（买入持有）
        self.results['benchmark'] = self._run_benchmark(
            price_file, start_date, end_date
        )

        return self.results

    def _add_analyzers(self, cerebro):
        """
        添加Backtrader分析器

        Parameters:
        -----------
        cerebro : Cerebro
            Backtrader引擎
        """
        # 返回率分析器
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

        # 夏普比率分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0)

        # 回撤分析器
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

        # 交易分析器
        cerebro.addanalyzer(bt.analyzers.Trades, _name='trades')

    def _run_benchmark(
        self,
        price_file: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        运行基准策略（买入持有）

        Parameters:
        -----------
        price_file : str
            价格数据文件
        start_date : str, optional
            开始日期
        end_date : str, optional
            结束日期

        Returns:
        --------
        dict
            基准策略结果
        """
        cerebro = bt.Cerebro()

        # 设置初始资金
        cerebro.broker.setcash(self.initial_cash)

        # 设置佣金
        cerebro.broker.setcommission(commission=self.commission)

        # 加载数据
        price_data = self.data_factory.load_price_data(price_file, start_date, end_date)
        data_feed = bt.feeds.PandasData(dataname=price_data)
        cerebro.adddata(data_feed)

        # 添加买入持有策略
        cerebro.addstrategy(BuyAndHoldStrategy)

        # 添加分析器
        self._add_analyzers(cerebro)

        # 运行回测
        results = cerebro.run()
        strategy = results[0]

        return {
            'strategy': strategy,
            'cerebro': cerebro,
            'final_value': cerebro.broker.getvalue(),
            'metrics': strategy.get_performance_metrics()
        }

    def compare_results(self) -> pd.DataFrame:
        """
        对比策略和基准的绩效

        Returns:
        --------
        DataFrame
            绩效对比表
        """
        if self.results is None:
            raise ValueError("尚未运行回测，请先调用run_backtest()")

        # 提取绩效指标
        strategy_metrics = self.results['metrics']
        benchmark_metrics = self.results['benchmark']['metrics']

        # 创建对比表
        comparison = pd.DataFrame({
            '指标': [
                '总收益率',
                '年化收益率',
                '夏普比率',
                '最大回撤',
                '最终资产'
            ],
            '宏观策略': [
                f"{strategy_metrics.get('total_return', 0):.2%}",
                f"{strategy_metrics.get('annual_return', 0):.2%}",
                f"{strategy_metrics.get('sharpe_ratio', 0):.2f}",
                f"{strategy_metrics.get('max_drawdown', 0):.2%}",
                f"{strategy_metrics.get('final_equity', 0):.2f}"
            ],
            '买入持有': [
                f"{benchmark_metrics.get('total_return', 0):.2%}",
                f"{benchmark_metrics.get('annual_return', 0):.2%}",
                f"{benchmark_metrics.get('sharpe_ratio', 0):.2f}",
                f"{benchmark_metrics.get('max_drawdown', 0):.2%}",
                f"{benchmark_metrics.get('final_equity', 0):.2f}"
            ]
        })

        return comparison

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        生成回测报告

        Parameters:
        -----------
        output_file : str, optional
            输出文件路径

        Returns:
        --------
        str
            报告内容
        """
        if self.results is None:
            raise ValueError("尚未运行回测，请先调用run_backtest()")

        # 生成对比表
        comparison = self.compare_results()

        # 生成报告
        report = []
        report.append("=" * 80)
        report.append("宏观策略回测报告")
        report.append("=" * 80)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"初始资金: {self.initial_cash:,.2f}")
        report.append("")

        # 绩效对比
        report.append("绩效对比:")
        report.append("-" * 80)
        report.append(comparison.to_string(index=False))
        report.append("")

        # 超额收益
        strategy_return = self.results['metrics'].get('total_return', 0)
        benchmark_return = self.results['benchmark']['metrics'].get('total_return', 0)
        excess_return = strategy_return - benchmark_return

        report.append("超额收益:")
        report.append("-" * 80)
        report.append(f"超额收益率: {excess_return:.2%}")
        report.append("")

        # 交易统计
        report.append("交易统计:")
        report.append("-" * 80)
        strategy = self.results['strategy']
        if hasattr(strategy, 'equity_curve') and len(strategy.equity_curve) > 0:
            report.append(f"交易次数: {strategy.signals_history.count(1) + strategy.signals_history.count(-1)}")
            report.append(f"回测天数: {len(strategy.equity_curve)}")

        report.append("")
        report.append("=" * 80)

        report_text = "\n".join(report)

        # 保存到文件
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"报告已保存到: {output_file}")

        return report_text

    def plot_results(self, save_path: Optional[str] = None):
        """
        绘制回测结果

        Parameters:
        -----------
        save_path : str, optional
            保存路径
        """
        if self.results is None:
            raise ValueError("尚未运行回测，请先调用run_backtest()")

        cerebro = self.results['cerebro']

        # 绘图
        import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 8))

        # 绘制权益曲线
        strategy = self.results['strategy']
        if hasattr(strategy, 'equity_curve') and len(strategy.equity_curve) > 0:
            equity_df = pd.DataFrame(strategy.equity_curve)
            equity_df.set_index('date', inplace=True)

            plt.plot(equity_df.index, equity_df['equity'], label='宏观策略', linewidth=2)

            # 绘制基准
            benchmark = self.results['benchmark']['strategy']
            if hasattr(benchmark, 'equity_curve') and len(benchmark.equity_curve) > 0:
                benchmark_df = pd.DataFrame(benchmark.equity_curve)
                benchmark_df.set_index('date', inplace=True)
                plt.plot(benchmark_df.index, benchmark_df['equity'], label='买入持有', linewidth=2, alpha=0.6)

        plt.title('宏观策略 vs 买入持有', fontsize=14, fontweight='bold')
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('资产净值', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        else:
            plt.show()


# 便捷函数
def run_macro_backtest(
    price_file: str,
    macro_file: Optional[str] = None,
    risk_file: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    initial_cash: float = 1000000.0,
    output_report: Optional[str] = None
) -> Dict:
    """
    便捷函数：运行宏观策略回测

    Parameters:
    -----------
    price_file : str
        价格数据文件
    macro_file : str, optional
        宏观数据文件
    risk_file : str, optional
        风险数据文件
    start_date : str, optional
        开始日期
    end_date : str, optional
        结束日期
    initial_cash : float
        初始资金
    output_report : str, optional
        报告输出路径

    Returns:
    --------
    dict
        回测结果
    """
    engine = BacktestEngine(initial_cash=initial_cash)

    # 运行回测
    results = engine.run_backtest(
        price_file=price_file,
        macro_file=macro_file,
        risk_file=risk_file,
        start_date=start_date,
        end_date=end_date
    )

    # 生成报告
    if output_report:
        engine.generate_report(output_report)

    return results
