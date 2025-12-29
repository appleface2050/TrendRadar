"""
行业选择器

基于宏观状态、宏观因子边际变化和行业动量，筛选行业并确定权重

功能：
1. 根据宏观状态筛选行业池
2. 结合宏观因子边际变化二次筛选
3. 引入行业动量确认
4. 输出行业权重建议
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not installed")

from strategies.rotation.industry_macro_db import IndustryMacroDB


class IndustrySelector:
    """
    行业选择器

    根据宏观状态和因子变化选择行业
    """

    def __init__(
        self,
        macro_db: Optional[IndustryMacroDB] = None,
        momentum_window: int = 20,
        rebalance_freq: str = 'M'
    ):
        """
        初始化行业选择器

        Parameters:
        -----------
        macro_db : IndustryMacroDB, optional
            宏观状态-行业数据库
        momentum_window : int
            动量窗口（默认20个交易日）
        rebalance_freq : str
            调仓频率：'M'=月度, 'Q'=季度
        """
        self.macro_db = macro_db
        self.momentum_window = momentum_window
        self.rebalance_freq = rebalance_freq

        # 选择历史
        self.selection_history = []

    def select_by_regime(
        self,
        current_regime: str,
        top_n: int = 5,
        metric: str = 'sharpe_ratio'
    ) -> List[str]:
        """
        根据宏观状态筛选行业

        Parameters:
        -----------
        current_regime : str
            当前宏观状态（Regime_1, Regime_2, ...）
        top_n : int
            选择前N个行业
        metric : str
            排序指标

        Returns:
        --------
        list
            选中的行业列表
        """
        if self.macro_db is None:
            raise ValueError("需要先加载 IndustryMacroDB")

        # 获取区制排名
        ranking = self.macro_db.get_regime_ranking(
            regime=current_regime,
            metric=metric,
            top_n=top_n
        )

        selected_industries = ranking['industry'].tolist()

        return selected_industries

    def filter_by_factor_change(
        self,
        industry_pool: List[str],
        factor_changes: Dict[str, float],
        sensitivities: Optional[Dict[str, Dict[str, float]]] = None
    ) -> List[str]:
        """
        根据宏观因子边际变化筛选行业

        Parameters:
        -----------
        industry_pool : list
            初选行业池
        factor_changes : dict
            因子变化，例如：{'growth': 0.5, 'inflation': -0.3, 'liquidity': 0.2}
        sensitivities : dict, optional
            行业对因子的敏感度
            格式：{'行业': {'growth': 0.5, 'inflation': -0.2, ...}, ...}
            如果为None，使用默认敏感度

        Returns:
        --------
        list
            筛选后的行业列表
        """
        # 默认敏感度（示例数据）
        if sensitivities is None:
            sensitivities = self._get_default_sensitivities()

        # 计算每个行业的综合得分
        industry_scores = {}

        for industry in industry_pool:
            if industry not in sensitivities:
                continue

            score = 0.0
            sensitivity = sensitivities[industry]

            for factor, change in factor_changes.items():
                if factor in sensitivity:
                    # 因子变化 × 敏感度
                    score += change * sensitivity[factor]

            industry_scores[industry] = score

        # 选择得分最高的行业（得分>0）
        selected = [
            industry for industry, score in industry_scores.items()
            if score > 0
        ]

        # 按得分排序
        selected.sort(key=lambda x: industry_scores[x], reverse=True)

        return selected if selected else industry_pool

    def confirm_by_momentum(
        self,
        industry_pool: List[str],
        industry_prices: Dict[str, pd.Series],
        n_top: int = 3
    ) -> List[str]:
        """
        使用行业动量确认筛选

        Parameters:
        -----------
        industry_pool : list
            行业池
        industry_prices : dict
            行业价格序列
        n_top : int
            选择动量最强的前N个行业

        Returns:
        --------
        list
            最终选中的行业
        """
        momentum_scores = {}

        for industry in industry_pool:
            if industry not in industry_prices:
                continue

            prices = industry_prices[industry]

            # 计算动量（过去N天的累计收益率）
            if len(prices) >= self.momentum_window:
                momentum = (prices.iloc[-1] / prices.iloc[-self.momentum_window]) - 1
                momentum_scores[industry] = momentum

        # 选择动量最强的前N个
        sorted_industries = sorted(
            momentum_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        selected = [industry for industry, _ in sorted_industries[:n_top]]

        return selected

    def calculate_weights(
        self,
        selected_industries: List[str],
        method: str = 'equal',
        industry_scores: Optional[Dict[str, float]] = None,
        min_weight: float = 0.10,
        max_weight: float = 0.40
    ) -> Dict[str, float]:
        """
        计算行业权重

        Parameters:
        -----------
        selected_industries : list
            选中的行业列表
        method : str
            权重方法：'equal', 'score', 'momentum', 'regime'
        industry_scores : dict, optional
            行业得分（用于score方法）
        min_weight : float
            最小权重
        max_weight : float
            最大权重

        Returns:
        --------
        dict
            行业权重
        """
        if method == 'equal':
            # 等权配置
            weight = 1.0 / len(selected_industries)
            weights = {industry: weight for industry in selected_industries}

        elif method == 'score' and industry_scores is not None:
            # 根据得分加权
            scores = np.array([
                industry_scores.get(industry, 0)
                for industry in selected_industries
            ])

            # 归一化
            weights_arr = scores / scores.sum() if scores.sum() > 0 else None

            if weights_arr is not None:
                # 限制权重范围
                weights_arr = np.clip(weights_arr, min_weight, max_weight)
                weights_arr = weights_arr / weights_arr.sum()

                weights = {
                    industry: weights_arr[i]
                    for i, industry in enumerate(selected_industries)
                }
            else:
                # 如果得分为0，使用等权
                weight = 1.0 / len(selected_industries)
                weights = {industry: weight for industry in selected_industries}

        elif method == 'regime' and self.macro_db is not None:
            # 使用区制数据库的权重
            current_regime = self._infer_current_regime()
            if current_regime:
                weights = self.macro_db.get_industry_allocation(
                    current_regime,
                    method='weighted',
                    top_n=len(selected_industries),
                    min_weight=min_weight,
                    max_weight=max_weight
                )
            else:
                # 如果无法推断区制，使用等权
                weight = 1.0 / len(selected_industries)
                weights = {industry: weight for industry in selected_industries}

        else:
            # 默认等权
            weight = 1.0 / len(selected_industries)
            weights = {industry: weight for industry in selected_industries}

        return weights

    def select_and_weight(
        self,
        current_regime: str,
        factor_changes: Dict[str, float],
        industry_prices: Dict[str, pd.Series],
        regime_top_n: int = 8,
        final_top_n: int = 3,
        weight_method: str = 'regime'
    ) -> Dict[str, float]:
        """
        完整的选择和权重流程

        Parameters:
        -----------
        current_regime : str
            当前宏观状态
        factor_changes : dict
            因子变化
        industry_prices : dict
            行业价格
        regime_top_n : int
            区制筛选阶段选择数量
        final_top_n : int
            最终选择数量
        weight_method : str
            权重方法

        Returns:
        --------
        dict
            行业权重
        """
        # 1. 根据宏观状态筛选
        step1_industries = self.select_by_regime(
            current_regime=current_regime,
            top_n=regime_top_n
        )

        # 2. 根据因子变化筛选
        step2_industries = self.filter_by_factor_change(
            industry_pool=step1_industries,
            factor_changes=factor_changes
        )

        # 3. 动量确认
        step3_industries = self.confirm_by_momentum(
            industry_pool=step2_industries,
            industry_prices=industry_prices,
            n_top=final_top_n
        )

        # 4. 计算权重
        weights = self.calculate_weights(
            selected_industries=step3_industries,
            method=weight_method
        )

        # 记录选择历史
        self.selection_history.append({
            'date': datetime.now(),
            'regime': current_regime,
            'selected_industries': step3_industries,
            'weights': weights
        })

        return weights

    def get_selection_summary(self) -> pd.DataFrame:
        """
        获取选择历史摘要

        Returns:
        --------
        DataFrame
            选择历史
        """
        if not self.selection_history:
            return pd.DataFrame()

        df = pd.DataFrame(self.selection_history)
        return df

    def _get_default_sensitivities(self) -> Dict[str, Dict[str, float]]:
        """
        获取默认的行业-因子敏感度

        Returns:
        --------
        dict
            敏感度矩阵
        """
        # 示例敏感度数据（实际应该从历史数据估计）
        sensitivities = {
            '金融': {
                'growth': 0.6,
                'inflation': -0.3,
                'liquidity': 0.5
            },
            '科技': {
                'growth': 0.8,
                'inflation': -0.2,
                'liquidity': 0.4
            },
            '消费': {
                'growth': 0.5,
                'inflation': -0.1,
                'liquidity': 0.3
            },
            '工业': {
                'growth': 0.7,
                'inflation': -0.4,
                'liquidity': 0.6
            },
            '能源': {
                'growth': 0.3,
                'inflation': 0.5,
                'liquidity': 0.2
            },
            '材料': {
                'growth': 0.6,
                'inflation': 0.3,
                'liquidity': 0.4
            },
            '医药': {
                'growth': 0.4,
                'inflation': -0.2,
                'liquidity': 0.3
            },
            '公用': {
                'growth': 0.2,
                'inflation': -0.5,
                'liquidity': 0.6
            }
        }

        return sensitivities

    def _infer_current_regime(self) -> Optional[str]:
        """
        推断当前区制

        Returns:
        --------
        str or None
            区制名称
        """
        # 如果有数据库，从最新记录推断
        if self.macro_db and hasattr(self.macro_db, 'regime_sequence'):
            if not self.macro_db.regime_sequence.empty:
                return self.macro_db.regime_sequence.iloc[-1]

        return None


# 便捷函数
def select_industries(
    current_regime: str,
    factor_changes: Dict[str, float],
    industry_prices: Dict[str, pd.Series],
    macro_db: Optional[IndustryMacroDB] = None
) -> Dict[str, float]:
    """
    便捷函数：选择行业并计算权重

    Parameters:
    -----------
    current_regime : str
        当前宏观状态
    factor_changes : dict
        因子变化
    industry_prices : dict
        行业价格
    macro_db : IndustryMacroDB, optional
        宏观数据库

    Returns:
    --------
    dict
        行业权重
    """
    selector = IndustrySelector(macro_db=macro_db)

    return selector.select_and_weight(
        current_regime=current_regime,
        factor_changes=factor_changes,
        industry_prices=industry_prices
    )
