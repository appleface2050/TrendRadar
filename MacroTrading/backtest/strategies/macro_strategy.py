"""
Backtrader宏观策略

基于宏观多因子打分系统的择时策略

功能：
1. 根据宏观得分生成交易信号
2. 动态调整仓位
3. 风险管理
4. 绩效跟踪
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, List
import warnings
warnings.filterwarnings('ignore')

try:
    import backtrader as bt
    BACKTRADER_AVAILABLE = True
except ImportError:
    BACKTRADER_AVAILABLE = False
    print("Warning: backtrader not installed")

from strategies.timing.macro_scorecard import MacroScorecard
from strategies.timing.signal_generator import SignalGenerator


class MacroStrategy(bt.Strategy):
    """
    宏观择时策略

    基于宏观多因子打分系统进行择时
    """

    params = (
        # 宏观得分权重
        ('macro_weight', 0.30),
        ('liquidity_weight', 0.25),
        ('valuation_weight', 0.25),
        ('sentiment_weight', 0.20),
        # 信号参数
        ('score_threshold_low', 35),
        ('score_threshold_high', 65),
        ('position_threshold', 0.05),
        # 风险管理
        ('risk_adjustment', True),
        ('risk_threshold_high', 70),
        ('max_position', 1.0),
        ('min_position', 0.0),
        # 其他
        ('printlog', True),
    )

    def __init__(self):
        """初始化策略"""
        # 保存数据引用
        self.dataclose = self.datas[0].close
        self.datavolume = self.datas[0].volume

        # 检查数据是否包含宏观数据
        self.has_macro = hasattr(self.datas[0], 'macro_score')
        self.has_risk = hasattr(self.datas[0], 'risk_index')

        # 订单相关
        self.order = None
        self.buy_price = None
        self.buy_comm = None

        # 绩效跟踪
        self.equity_curve = []
        self.drawdowns = []

        # 宏观得分卡和信号生成器
        self.scorecard = MacroScorecard(
            macro_weight=self.params.macro_weight,
            liquidity_weight=self.params.liquidity_weight,
            valuation_weight=self.params.valuation_weight,
            sentiment_weight=self.params.sentiment_weight
        )

        self.signal_gen = SignalGenerator(
            risk_adjustment=self.params.risk_adjustment
        )

        # 历史数据容器
        self.macro_scores_history = []
        self.positions_history = []
        self.signals_history = []

    def next(self):
        """
        每个bar调用一次

        这是策略的核心逻辑
        """
        # 如果有未完成订单，不操作
        if self.order:
            return

        # 如果数据包含宏观数据，使用宏观信号
        if self.has_macro:
            self._macro_logic()
        else:
            # 否则使用简单的技术指标逻辑
            self._simple_logic()

        # 记录绩效
        self._track_performance()

    def _macro_logic(self):
        """基于宏观因子的交易逻辑"""
        # 获取当前宏观数据
        current_date = len(self.data)
        macro_score = self.datas[0].macro_score[0]

        # 计算目标仓位
        if macro_score < self.params.score_threshold_low:
            # 低得分：低仓位
            target_position = self.params.min_position
        elif macro_score > self.params.score_threshold_high:
            # 高得分：高仓位
            target_position = self.params.max_position
        else:
            # 中等得分：中等仓位
            target_position = 0.50

        # 风险调整（如果启用）
        if self.params.risk_adjustment and self.has_risk:
            risk_index = self.datas[0].risk_index[0]
            if risk_index > self.params.risk_threshold_high:
                target_position *= 0.5  # 高风险：减仓一半

        # 记录
        self.macro_scores_history.append(macro_score)
        self.positions_history.append(target_position)

        # 生成交易信号
        current_position = self.position.size / self.params.max_position
        position_change = target_position - current_position

        if abs(position_change) > self.params.position_threshold:
            if position_change > 0:
                # 买入信号
                self._buy(target_position)
            else:
                # 卖出信号
                self._sell(target_position)
        else:
            # 持有
            self.signals_history.append(0)

    def _simple_logic(self):
        """简单交易逻辑（当没有宏观数据时）"""
        # 计算简单移动平均线
        if len(self.data) < 20:
            return

        ma_short = bt.indicators.SMA(self.data.close, period=20)
        ma_long = bt.indicators.SMA(self.data.close, period=60)

        # 金叉买入，死叉卖出
        if self.position.size == 0:
            if ma_short[0] > ma_long[0]:
                self._buy(1.0)
        else:
            if ma_short[0] < ma_long[0]:
                self._sell(0.0)

    def _buy(self, target_position: float):
        """执行买入"""
        # 计算买入数量
        current_size = self.position.size
        target_size = target_position * self.params.max_position

        # 计算需要买入的数量
        buy_size = target_size - current_size

        if buy_size > 0:
            # 计算买入金额
            buy_value = self.broker.getvalue() * buy_size / self.params.max_position

            # 执行买入
            self.order = self.buy(size=buy_size)
            self.signals_history.append(1)

            if self.params.printlog:
                self.log(
                    f"买入: 价格={self.dataclose[0]:.2f}, "
                    f"仓位={target_position:.2%}, "
                    f"数量={buy_size:.2f}"
                )

    def _sell(self, target_position: float):
        """执行卖出"""
        # 计算卖出数量
        current_size = self.position.size
        target_size = target_position * self.params.max_position

        # 计算需要卖出的数量
        sell_size = current_size - target_size

        if sell_size > 0:
            # 执行卖出
            self.order = self.sell(size=sell_size)
            self.signals_history.append(-1)

            if self.params.printlog:
                self.log(
                    f"卖出: 价格={self.dataclose[0]:.2f}, "
                    f"仓位={target_position:.2%}, "
                    f"数量={sell_size:.2f}"
                )

    def _track_performance(self):
        """跟踪绩效"""
        # 记录权益
        self.equity_curve.append({
            'date': self.data.datetime.date(0),
            'equity': self.broker.getvalue(),
            'position': self.position.size
        })

        # 计算回撤
        if len(self.equity_curve) > 1:
            peak = max([e['equity'] for e in self.equity_curve])
            current = self.broker.getvalue()
            drawdown = (current - peak) / peak
            self.drawdowns.append(drawdown)

    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm

                if self.params.printlog:
                    self.log(
                        f"买入执行: 价格={order.executed.price:.2f}, "
                        f"成本={order.executed.value:.2f}, "
                        f"佣金={order.executed.comm:.2f}"
                    )
            else:
                if self.params.printlog:
                    self.log(
                        f"卖出执行: 价格={order.executed.price:.2f}, "
                        f"成本={order.executed.value:.2f}, "
                        f"佣金={order.executed.comm:.2f}"
                    )

        self.order = None

    def notify_trade(self, trade):
        """交易通知"""
        if not trade.isclosed:
            return

        if self.params.printlog:
            self.log(
                f"交易利润: 毛利润={trade.pnl:.2f}, 净利润={trade.pnlcomm:.2f}"
            )

    def stop(self):
        """策略停止时调用"""
        if self.params.printlog:
            final_value = self.broker.getvalue()
            self.log(f"最终资产: {final_value:.2f}")

            if len(self.equity_curve) > 0:
                initial_value = self.equity_curve[0]['equity']
                total_return = (final_value - initial_value) / initial_value
                self.log(f"总收益率: {total_return:.2%}")

    def log(self, txt, dt=None):
        """日志输出"""
        if self.params.printlog:
            dt = dt or self.data.datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def get_performance_metrics(self) -> Dict:
        """
        获取绩效指标

        Returns:
        --------
        dict
            包含收益率、夏普、最大回撤等
        """
        if len(self.equity_curve) < 2:
            return {}

        # 提取权益曲线
        equity_values = [e['equity'] for e in self.equity_curve]

        # 计算收益率
        returns = pd.Series(equity_values).pct_change().dropna()

        # 年化收益率
        total_return = (equity_values[-1] - equity_values[0]) / equity_values[0]
        n_days = len(equity_values)
        annual_return = (1 + total_return) ** (252 / n_days) - 1

        # 夏普比率
        if len(returns) > 0:
            sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        else:
            sharpe = 0

        # 最大回撤
        max_drawdown = min(self.drawdowns) if len(self.drawdowns) > 0 else 0

        # 胜率
        if len(self.signals_history) > 0:
            buy_signals = sum(1 for s in self.signals_history if s == 1)
            sell_signals = sum(1 for s in self.signals_history if s == -1)
            total_signals = buy_signals + sell_signals
            win_rate = 0.5  # 简化，实际需要计算每笔交易的盈亏
        else:
            win_rate = 0

        metrics = {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'final_equity': equity_values[-1],
            'total_trades': len(self.signals_history)
        }

        return metrics


class BuyAndHoldStrategy(bt.Strategy):
    """
    买入持有策略（作为基准）
    """

    params = (
        ('printlog', True),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None

    def next(self):
        """每个bar调用一次"""
        if self.order:
            return

        # 第一个bar买入
        if self.position.size == 0:
            self.order = self.buy(size=1.0)

    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed] and order.isbuy():
            if self.params.printlog:
                self.log(f"买入持有: 价格={order.executed.price:.2f}")

        self.order = None

    def log(self, txt, dt=None):
        """日志输出"""
        if self.params.printlog:
            dt = dt or self.data.datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
