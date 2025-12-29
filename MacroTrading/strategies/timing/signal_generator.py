"""
宏观择时信号生成器

根据多因子得分和风险指数，生成仓位建议和交易信号

功能：
1. 将综合得分转换为仓位建议（0%-100%）
2. 根据风险指数动态调整仓位
3. 生成交易信号（买入/卖出/持有）
4. 信号平滑处理（避免频繁交易）
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import warnings
warnings.filterwarnings('ignore')

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: scipy not installed")


class SignalGenerator:
    """
    宏观择时信号生成器

    将宏观得分转换为可执行的交易信号
    """

    def __init__(
        self,
        score_thresholds: Dict[str, float] = None,
        position_levels: Dict[str, float] = None,
        risk_adjustment: bool = True,
        signal_smoothing: bool = True,
        smoothing_window: int = 5
    ):
        """
        初始化信号生成器

        Parameters:
        -----------
        score_thresholds : dict, optional
            得分阈值，例如：{'low': 30, 'medium': 50, 'high': 70}
            默认：{'low': 30, 'medium': 50, 'high': 70}
        position_levels : dict, optional
            仓位水平，例如：{'low': 0.2, 'medium': 0.5, 'high': 0.8, 'very_high': 1.0}
            默认：{'low': 0.2, 'medium': 0.5, 'high': 0.8, 'very_high': 1.0}
        risk_adjustment : bool
            是否根据风险指数调整仓位（默认True）
        signal_smoothing : bool
            是否对信号进行平滑处理（默认True）
        smoothing_window : int
            平滑窗口大小（默认5天）
        """
        # 得分阈值
        if score_thresholds is None:
            self.score_thresholds = {
                'very_low': 20,
                'low': 35,
                'medium': 50,
                'high': 65,
                'very_high': 80
            }
        else:
            self.score_thresholds = score_thresholds

        # 仓位水平
        if position_levels is None:
            self.position_levels = {
                'very_low': 0.0,
                'low': 0.25,
                'medium': 0.50,
                'high': 0.75,
                'very_high': 1.0
            }
        else:
            self.position_levels = position_levels

        self.risk_adjustment = risk_adjustment
        self.signal_smoothing = signal_smoothing
        self.smoothing_window = smoothing_window

        # 信号历史
        self.signals = None
        self.positions = None
        self.risk_adjusted_positions = None

    def score_to_position(self, composite_score: pd.Series) -> pd.Series:
        """
        将综合得分转换为仓位建议

        Parameters:
        -----------
        composite_score : Series
            综合得分（0-100）

        Returns:
        --------
        Series
            仓位建议（0.0-1.0）
        """
        position = pd.Series(0.0, index=composite_score.index)

        # 根据得分区间设置仓位
        position[composite_score < self.score_thresholds['very_low']] = self.position_levels['very_low']
        position[
            (composite_score >= self.score_thresholds['very_low']) &
            (composite_score < self.score_thresholds['low'])
        ] = self.position_levels['low']
        position[
            (composite_score >= self.score_thresholds['low']) &
            (composite_score < self.score_thresholds['medium'])
        ] = self.position_levels['medium']
        position[
            (composite_score >= self.score_thresholds['medium']) &
            (composite_score < self.score_thresholds['high'])
        ] = self.position_levels['high']
        position[composite_score >= self.score_thresholds['very_high']] = self.position_levels['very_high']
        position[
            (composite_score >= self.score_thresholds['high']) &
            (composite_score < self.score_thresholds['very_high'])
        ] = 0.875  # (0.75 + 1.0) / 2

        self.positions = position
        return position

    def adjust_for_risk(
        self,
        position: pd.Series,
        risk_index: pd.Series,
        risk_thresholds: Dict[str, float] = None
    ) -> pd.Series:
        """
        根据风险指数调整仓位

        Parameters:
        -----------
        position : Series
            原始仓位
        risk_index : Series
            风险指数（0-100）
        risk_thresholds : dict, optional
            风险阈值，例如：{'low': 20, 'medium': 40, 'high': 70}
            默认：{'low': 20, 'medium': 40, 'high': 70}

        Returns:
        --------
        Series
            风险调整后的仓位
        """
        if risk_thresholds is None:
            risk_thresholds = {
                'low': 20,
                'medium': 40,
                'high': 70
            }

        adjusted_position = position.copy()

        # 高风险：缩减仓位至50%
        high_risk = risk_index >= risk_thresholds['high']
        adjusted_position[high_risk] = position[high_risk] * 0.5

        # 中等风险：缩减仓位至75%
        medium_risk = (
            (risk_index >= risk_thresholds['medium']) &
            (risk_index < risk_thresholds['high'])
        )
        adjusted_position[medium_risk] = position[medium_risk] * 0.75

        # 低风险：保持仓位不变
        # low_risk = risk_index < risk_thresholds['medium']

        self.risk_adjusted_positions = adjusted_position
        return adjusted_position

    def generate_signals(
        self,
        position: pd.Series,
        threshold: float = 0.05
    ) -> pd.Series:
        """
        生成交易信号

        Parameters:
        -----------
        position : Series
            仓位序列
        threshold : float
            变化阈值（默认0.05，即5%）

        Returns:
        --------
        Series
            交易信号：1=买入, -1=卖出, 0=持有
        """
        # 计算仓位变化
        position_change = position.diff()

        # 生成信号
        signals = pd.Series(0, index=position.index)

        # 买入信号：仓位增加超过阈值
        signals[position_change > threshold] = 1

        # 卖出信号：仓位减少超过阈值
        signals[position_change < -threshold] = -1

        # 持有信号：变化小于阈值
        signals[np.abs(position_change) <= threshold] = 0

        # 如果启用了信号平滑
        if self.signal_smoothing and self.smoothing_window > 1:
            signals = self._smooth_signals(signals, window=self.smoothing_window)

        self.signals = signals
        return signals

    def _smooth_signals(self, signals: pd.Series, window: int = 5) -> pd.Series:
        """
        平滑信号（避免频繁交易）

        使用多数投票法：在窗口期内，出现最多的信号作为最终信号
        """
        smoothed = signals.copy()

        for i in range(window, len(signals)):
            window_signals = signals.iloc[i-window:i]
            # 统计各类信号数量
            signal_counts = window_signals.value_counts()

            if len(signal_counts) > 0:
                # 选择出现最多的信号
                dominant_signal = signal_counts.idxmax()
                smoothed.iloc[i] = dominant_signal

        return smoothed

    def generate_trading_orders(
        self,
        signals: pd.Series,
        current_position: float = 0.0
    ) -> pd.DataFrame:
        """
        生成交易指令

        Parameters:
        -----------
        signals : Series
            交易信号
        current_position : float
            当前仓位（默认0.0）

        Returns:
        --------
        DataFrame
            交易指令，包含列：date, signal, target_position, action, quantity
        """
        orders = pd.DataFrame(index=signals.index)
        orders['signal'] = signals

        # 记录目标仓位
        target_position = current_position
        target_positions = []

        for i, signal in enumerate(signals):
            if signal == 1:  # 买入
                target_position = min(target_position + 0.25, 1.0)
            elif signal == -1:  # 卖出
                target_position = max(target_position - 0.25, 0.0)
            # 持有不变

            target_positions.append(target_position)

        orders['target_position'] = target_positions

        # 生成交易动作
        position_change = pd.Series(target_positions).diff()
        orders['action'] = 'hold'
        orders[position_change > 0] = 'buy'
        orders[position_change < 0] = 'sell'
        orders['quantity'] = np.abs(position_change)

        return orders

    def generate_all(
        self,
        composite_score: pd.Series,
        risk_index: Optional[pd.Series] = None,
        signal_threshold: float = 0.05
    ) -> Dict[str, pd.Series]:
        """
        一站式生成所有信号

        Parameters:
        -----------
        composite_score : Series
            综合得分
        risk_index : Series, optional
            风险指数
        signal_threshold : float
            信号变化阈值

        Returns:
        --------
        dict
            包含：position, risk_adjusted_position, signals, orders
        """
        # 1. 得分转仓位
        position = self.score_to_position(composite_score)

        # 2. 风险调整（如果提供风险指数）
        if risk_index is not None and self.risk_adjustment:
            final_position = self.adjust_for_risk(position, risk_index)
        else:
            final_position = position

        # 3. 生成交易信号
        signals = self.generate_signals(final_position, threshold=signal_threshold)

        # 4. 生成交易指令
        orders = self.generate_trading_orders(signals)

        return {
            'position': position,
            'risk_adjusted_position': final_position,
            'signals': signals,
            'orders': orders
        }

    def backtest_signals(
        self,
        signals: pd.Series,
        returns: pd.Series,
        initial_capital: float = 1000000.0
    ) -> pd.DataFrame:
        """
        简单回测交易信号

        Parameters:
        -----------
        signals : Series
            交易信号
        returns : Series
            资产收益率
        initial_capital : float
            初始资金

        Returns:
        --------
        DataFrame
            包含净值、收益率等
        """
        # 对齐索引
        common_index = signals.index.intersection(returns.index)
        signals_aligned = signals.loc[common_index]
        returns_aligned = returns.loc[common_index]

        # 初始化
        capital = initial_capital
        position = 0.0  # 0-1之间
        equity_curve = []

        for i, (date, signal) in enumerate(signals_aligned.items()):
            # 更新仓位
            if signal == 1:  # 买入
                position = min(position + 0.25, 1.0)
            elif signal == -1:  # 卖出
                position = max(position - 0.25, 0.0)

            # 计算当日收益
            daily_return = returns_aligned.iloc[i] * position
            capital *= (1 + daily_return)

            equity_curve.append({
                'date': date,
                'signal': signal,
                'position': position,
                'daily_return': daily_return,
                'capital': capital
            })

        results = pd.DataFrame(equity_curve)
        results.set_index('date', inplace=True)

        return results

    def get_signal_summary(self, date: Optional[str] = None) -> Dict:
        """
        获取信号摘要

        Parameters:
        -----------
        date : str, optional
            日期（YYYY-MM-DD），如果为None则返回最新日期

        Returns:
        --------
        dict
            信号摘要
        """
        if date is None:
            if self.signals is not None:
                date = self.signals.index[-1]
            else:
                raise ValueError("没有可用的信号数据")

        # 信号映射
        signal_map = {
            1: '买入',
            -1: '卖出',
            0: '持有'
        }

        summary = {
            'date': date,
            'signal': signal_map.get(self.signals.get(date, 0), '持有'),
            'position': self.positions.get(date, 0.0) if self.positions is not None else 0.0,
            'risk_adjusted_position': self.risk_adjusted_positions.get(date, 0.0) if self.risk_adjusted_positions is not None else 0.0
        }

        return summary


# 便捷函数
def generate_timing_signals(
    composite_score: pd.Series,
    risk_index: Optional[pd.Series] = None,
    score_thresholds: Optional[Dict[str, float]] = None,
    risk_adjustment: bool = True
) -> Dict[str, pd.Series]:
    """
    便捷函数：生成择时信号

    Parameters:
    -----------
    composite_score : Series
        综合得分
    risk_index : Series, optional
        风险指数
    score_thresholds : dict, optional
        得分阈值
    risk_adjustment : bool
        是否进行风险调整

    Returns:
    --------
    dict
        包含所有信号
    """
    generator = SignalGenerator(
        score_thresholds=score_thresholds,
        risk_adjustment=risk_adjustment
    )

    return generator.generate_all(composite_score, risk_index)
