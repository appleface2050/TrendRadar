"""
宏观区制识别模型

包含中美两国独立的区制识别实现
"""

from .markov_switching import MacroRegimeModel
from .us_regime import USMarketRegimeModel
from .cn_regime import CNPolicyRegimeModel

__all__ = [
    'MacroRegimeModel',      # 基础区制模型（保留用于兼容）
    'USMarketRegimeModel',   # 美国市场区制模型（独立实现）
    'CNPolicyRegimeModel',   # 中国政策区制模型（独立实现）
]
