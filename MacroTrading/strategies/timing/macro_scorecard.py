"""
宏观多因子打分系统

整合四大类因子，生成综合宏观得分：
1. 宏观状态分：基于MS模型的状态概率
2. 流动性分：M1-M2剪刀差、社融增速
3. 估值分：股债风险溢价（ERP）
4. 外资情绪分：资金流Nowcasting

功能：
- 计算各类因子得分
- 动态权重调整
- 生成综合得分
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not installed")


class MacroScorecard:
    """
    宏观多因子打分系统

    将四类宏观因子标准化并加总，生成0-100的综合得分
    """

    def __init__(
        self,
        macro_weight: float = 0.30,
        liquidity_weight: float = 0.25,
        valuation_weight: float = 0.25,
        sentiment_weight: float = 0.20
    ):
        """
        初始化打分系统

        Parameters:
        -----------
        macro_weight : float
            宏观状态权重（默认0.30）
        liquidity_weight : float
            流动性因子权重（默认0.25）
        valuation_weight : float
            估值因子权重（默认0.25）
        sentiment_weight : float
            情绪因子权重（默认0.20）
        """
        # 权重参数
        self.macro_weight = macro_weight
        self.liquidity_weight = liquidity_weight
        self.valuation_weight = valuation_weight
        self.sentiment_weight = sentiment_weight

        # 标准化器
        if SKLEARN_AVAILABLE:
            self.scaler = StandardScaler()
        else:
            self.scaler = None

        # 因子数据
        self.macro_score = None
        self.liquidity_score = None
        self.valuation_score = None
        self.sentiment_score = None
        self.composite_score = None

        # 历史数据（用于标准化）
        self.historical_scores = {
            'macro': [],
            'liquidity': [],
            'valuation': [],
            'sentiment': []
        }

    def calculate_macro_score(
        self,
        regime_probs: pd.DataFrame,
        regime_weights: Optional[Dict[str, float]] = None
    ) -> pd.Series:
        """
        计算宏观状态得分

        Parameters:
        -----------
        regime_probs : DataFrame
            区制概率数据，列为各区制概率（Regime_1, Regime_2, ...）
        regime_weights : dict, optional
            各区制权重，例如：{'Regime_1': 100, 'Regime_2': 50, 'Regime_3': 0, 'Regime_4': -50}
            如果为None，使用默认权重

        Returns:
        --------
        Series
            宏观状态得分（0-100）
        """
        # 默认区制权重（基于经济含义）
        if regime_weights is None:
            # Regime_1: 正常增长（100分）
            # Regime_2: 过热（50分，经济好但有通胀压力）
            # Regime_3: 衰退（0分，最差）
            # Regime_4: 滞胀（25分，较差）
            regime_weights = {
                'Regime_1': 100,
                'Regime_2': 50,
                'Regime_3': 0,
                'Regime_4': 25
            }

        # 计算加权得分
        scores = pd.Series(0.0, index=regime_probs.index)

        for regime, weight in regime_weights.items():
            if regime in regime_probs.columns:
                scores += regime_probs[regime] * weight

        # 归一化到0-100
        min_score = scores.min()
        max_score = scores.max()

        if max_score > min_score:
            scores = (scores - min_score) / (max_score - min_score) * 100

        self.macro_score = scores
        return scores

    def calculate_liquidity_score(
        self,
        m1_data: pd.Series,
        m2_data: pd.Series,
        social_financing: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        计算流动性得分

        Parameters:
        -----------
        m1_data : Series
            M1货币供应量（同比增速）
        m2_data : Series
            M2货币供应量（同比增速）
        social_financing : Series, optional
            社融增速

        Returns:
        --------
        Series
            流动性得分（0-100）
        """
        # 计算M1-M2剪刀差
        m1_m2_diff = m1_data - m2_data

        # 标准化各指标
        scores = pd.DataFrame(index=m1_data.index)

        # M1增速（越高越好）
        scores['m1'] = m1_data

        # M2增速（适中最好，过高有通胀风险）
        scores['m2'] = m2_data

        # 剪刀差（正值表示M1增速快于M2，经济活跃）
        scores['diff'] = m1_m2_diff

        # 社融增速（如果提供）
        if social_financing is not None:
            scores['social_financing'] = social_financing

        # 标准化到0-100（使用滚动窗口）
        for col in scores.columns:
            rolling_mean = scores[col].rolling(window=252).mean()  # 1年窗口
            rolling_std = scores[col].rolling(window=252).std()

            # Z-score标准化
            z_score = (scores[col] - rolling_mean) / rolling_std

            # 转换到0-100（使用累积分布函数）
            scores[col] = self._zscore_to_percentile(z_score)

        # 加权平均（M1和剪刀差权重更高）
        if 'social_financing' in scores.columns:
            liquidity_score = (
                scores['m1'] * 0.30 +
                scores['diff'] * 0.40 +
                scores['social_financing'] * 0.30
            )
        else:
            liquidity_score = (
                scores['m1'] * 0.50 +
                scores['diff'] * 0.50
            )

        self.liquidity_score = liquidity_score
        return liquidity_score

    def calculate_valuation_score(
        self,
        stock_price: pd.Series,
        bond_yield: pd.Series,
        earnings_yield: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        计算估值得分（基于股债风险溢价ERP）

        Parameters:
        -----------
        stock_price : Series
            股票价格指数
        bond_yield : Series
            债券收益率（10年期国债）
        earnings_yield : Series, optional
            股票盈利收益率（1/PE）

        Returns:
        --------
        Series
            估值得分（0-100）
        """
        # 如果没有提供盈利收益率，使用价格倒数近似
        if earnings_yield is None:
            earnings_yield = 1.0 / stock_price

        # 计算股债风险溢价（ERP）
        # ERP = 股票盈利收益率 - 无风险收益率
        erp = earnings_yield - bond_yield

        # 标准化ERP
        rolling_mean = erp.rolling(window=252).mean()  # 1年窗口
        rolling_std = erp.rolling(window=252).std()

        z_score = (erp - rolling_mean) / rolling_std

        # 转换到0-100
        valuation_score = self._zscore_to_percentile(z_score)

        self.valuation_score = valuation_score
        return valuation_score

    def calculate_sentiment_score(
        self,
        northbound_flow: pd.Series,
        vix: Optional[pd.Series] = None,
        flow_prediction: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        计算外资情绪得分

        Parameters:
        -----------
        northbound_flow : Series
            北向资金流（正值为流入）
        vix : Series, optional
            VIX波动率指数
        flow_prediction : Series, optional
            资金流预测（未来N日）

        Returns:
        --------
        Series
            情绪得分（0-100）
        """
        scores = pd.DataFrame(index=northbound_flow.index)

        # 北向资金流（标准化）
        rolling_mean = northbound_flow.rolling(window=20).mean()
        rolling_std = northbound_flow.rolling(window=20).std()
        z_score = (northbound_flow - rolling_mean) / rolling_std
        scores['flow'] = self._zscore_to_percentile(z_score)

        # VIX指数（越低越好）
        if vix is not None:
            vix_mean = vix.rolling(window=20).mean()
            vix_std = vix.rolling(window=20).std()
            vix_z = (vix - vix_mean) / vix_std
            # VIX越低，情绪越好（反向）
            scores['vix'] = 100 - self._zscore_to_percentile(vix_z)

        # 资金流预测（如果提供）
        if flow_prediction is not None:
            flow_pred_mean = flow_prediction.rolling(window=20).mean()
            flow_pred_std = flow_prediction.rolling(window=20).std()
            flow_pred_z = (flow_prediction - flow_pred_mean) / flow_pred_std
            scores['prediction'] = self._zscore_to_percentile(flow_pred_z)

        # 加权平均
        if 'vix' in scores.columns and 'prediction' in scores.columns:
            sentiment_score = (
                scores['flow'] * 0.40 +
                scores['vix'] * 0.30 +
                scores['prediction'] * 0.30
            )
        elif 'vix' in scores.columns:
            sentiment_score = (
                scores['flow'] * 0.60 +
                scores['vix'] * 0.40
            )
        elif 'prediction' in scores.columns:
            sentiment_score = (
                scores['flow'] * 0.60 +
                scores['prediction'] * 0.40
            )
        else:
            sentiment_score = scores['flow']

        self.sentiment_score = sentiment_score
        return sentiment_score

    def calculate_composite_score(
        self,
        macro_score: Optional[pd.Series] = None,
        liquidity_score: Optional[pd.Series] = None,
        valuation_score: Optional[pd.Series] = None,
        sentiment_score: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        计算综合得分

        Parameters:
        -----------
        macro_score : Series, optional
            宏观状态得分
        liquidity_score : Series, optional
            流动性得分
        valuation_score : Series, optional
            估值得分
        sentiment_score : Series, optional
            情绪得分

        Returns:
        --------
        Series
            综合得分（0-100）
        """
        # 使用已计算的得分（如果没有提供）
        if macro_score is None:
            macro_score = self.macro_score
        if liquidity_score is None:
            liquidity_score = self.liquidity_score
        if valuation_score is None:
            valuation_score = self.valuation_score
        if sentiment_score is None:
            sentiment_score = self.sentiment_score

        # 检查所有得分是否都已计算
        scores_dict = {
            'macro': macro_score,
            'liquidity': liquidity_score,
            'valuation': valuation_score,
            'sentiment': sentiment_score
        }

        valid_scores = {k: v for k, v in scores_dict.items() if v is not None}

        if len(valid_scores) < 2:
            raise ValueError("至少需要2个因子得分才能计算综合得分")

        # 对齐索引
        common_index = valid_scores['macro'].index
        for score in valid_scores.values():
            common_index = common_index.intersection(score.index)

        # 加权求和
        composite = pd.Series(0.0, index=common_index)

        if 'macro' in valid_scores:
            composite += valid_scores['macro'][common_index] * self.macro_weight
        if 'liquidity' in valid_scores:
            composite += valid_scores['liquidity'][common_index] * self.liquidity_weight
        if 'valuation' in valid_scores:
            composite += valid_scores['valuation'][common_index] * self.valuation_weight
        if 'sentiment' in valid_scores:
            composite += valid_scores['sentiment'][common_index] * self.sentiment_weight

        # 重新归一化到0-100
        total_weight = (
            self.macro_weight * ('macro' in valid_scores) +
            self.liquidity_weight * ('liquidity' in valid_scores) +
            self.valuation_weight * ('valuation' in valid_scores) +
            self.sentiment_weight * ('sentiment' in valid_scores)
        )

        composite = composite / total_weight

        # 确保在0-100范围内
        composite = composite.clip(0, 100)

        self.composite_score = composite
        return composite

    def get_score_summary(self, date: Optional[str] = None) -> Dict:
        """
        获取得分摘要

        Parameters:
        -----------
        date : str, optional
            日期（YYYY-MM-DD），如果为None则返回最新日期

        Returns:
        --------
        dict
            各类因子得分
        """
        if date is None:
            if self.composite_score is not None:
                date = self.composite_score.index[-1]
            else:
                raise ValueError("没有可用的得分数据")

        summary = {
            'date': date,
            'macro_score': self.macro_score.get(date, None) if self.macro_score is not None else None,
            'liquidity_score': self.liquidity_score.get(date, None) if self.liquidity_score is not None else None,
            'valuation_score': self.valuation_score.get(date, None) if self.valuation_score is not None else None,
            'sentiment_score': self.sentiment_score.get(date, None) if self.sentiment_score is not None else None,
            'composite_score': self.composite_score.get(date, None) if self.composite_score is not None else None
        }

        return summary

    def _zscore_to_percentile(self, z_score: pd.Series) -> pd.Series:
        """
        将Z-score转换为百分位数（0-100）

        使用标准正态分布的累积分布函数
        """
        from scipy import stats

        percentile = stats.norm.cdf(z_score) * 100
        return percentile


# 便捷函数
def calculate_macro_scorecard(
    regime_probs: pd.DataFrame,
    m1_data: pd.Series,
    m2_data: pd.Series,
    stock_price: pd.Series,
    bond_yield: pd.Series,
    northbound_flow: pd.Series,
    social_financing: Optional[pd.Series] = None,
    vix: Optional[pd.Series] = None,
    weights: Optional[Dict[str, float]] = None
) -> Tuple[pd.Series, Dict[str, pd.Series]]:
    """
    一站式计算宏观得分卡

    Parameters:
    -----------
    regime_probs : DataFrame
        区制概率
    m1_data : Series
        M1货币供应量
    m2_data : Series
        M2货币供应量
    stock_price : Series
        股票价格
    bond_yield : Series
        债券收益率
    northbound_flow : Series
        北向资金流
    social_financing : Series, optional
        社融增速
    vix : Series, optional
        VIX指数
    weights : dict, optional
        因子权重

    Returns:
    --------
    composite_score : Series
        综合得分
    component_scores : dict
        各类因子得分
    """
    # 初始化打分系统
    if weights is not None:
        scorecard = MacroScorecard(
            macro_weight=weights.get('macro', 0.30),
            liquidity_weight=weights.get('liquidity', 0.25),
            valuation_weight=weights.get('valuation', 0.25),
            sentiment_weight=weights.get('sentiment', 0.20)
        )
    else:
        scorecard = MacroScorecard()

    # 计算各类得分
    macro_score = scorecard.calculate_macro_score(regime_probs)
    liquidity_score = scorecard.calculate_liquidity_score(m1_data, m2_data, social_financing)
    valuation_score = scorecard.calculate_valuation_score(stock_price, bond_yield)
    sentiment_score = scorecard.calculate_sentiment_score(northbound_flow, vix)

    # 计算综合得分
    composite_score = scorecard.calculate_composite_score(
        macro_score, liquidity_score, valuation_score, sentiment_score
    )

    component_scores = {
        'macro': macro_score,
        'liquidity': liquidity_score,
        'valuation': valuation_score,
        'sentiment': sentiment_score
    }

    return composite_score, component_scores
