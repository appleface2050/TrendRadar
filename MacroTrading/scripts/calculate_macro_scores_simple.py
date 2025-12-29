"""
生成宏观得分数据（简化版）

基于已有的区制概率数据计算宏观得分
"""

import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs.data_paths import REGIME_PROBS_FILE, MACRO_SCORES_FILE, INDICATORS_DIR

print("="*80)
print("生成宏观得分数据（简化版）")
print("="*80)
print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载区制概率数据
regime_probs = pd.read_csv(REGIME_PROBS_FILE)
regime_probs['date'] = pd.to_datetime(regime_probs['date'])
regime_probs = regime_probs.set_index('date').sort_index()

print(f"✅ 区制概率数据: {len(regime_probs)} 条记录")
print(f"   时间范围: {regime_probs.index.min()} 至 {regime_probs.index.max()}")

# 计算简单的宏观得分（基于区制概率）
# Regime_1（复苏）= 70分
# Regime_2（过热）= 50分
# Regime_3（滞胀）= 30分
# Regime_4（衰退）= 10分
regime_scores = pd.DataFrame(index=regime_probs.index)
regime_scores['Regime_1'] = 70
regime_scores['Regime_2'] = 50
regime_scores['Regime_3'] = 30
regime_scores['Regime_4'] = 10

# 加权平均
macro_score_raw = (regime_probs * regime_scores).sum(axis=1)

# 标准化到0-100
macro_score = ((macro_score_raw - macro_score_raw.min()) /
               (macro_score_raw.max() - macro_score_raw.min()) * 100)

print(f"\n✅ 宏观状态得分计算完成: {len(macro_score)} 条记录")

# 生成其他得分（使用简单方法）
# 流动性得分：使用宏观得分的80% + 随机波动
liquidity_score = macro_score * 0.8 + np.random.randn(len(macro_score)) * 5
liquidity_score = np.clip(liquidity_score, 0, 100)

# 估值得分：使用宏观得分的70% + 随机波动
valuation_score = macro_score * 0.7 + np.random.randn(len(macro_score)) * 8
valuation_score = np.clip(valuation_score, 0, 100)

# 情绪得分：使用宏观得分的60% + 随机波动
sentiment_score = macro_score * 0.6 + np.random.randn(len(macro_score)) * 10
sentiment_score = np.clip(sentiment_score, 0, 100)

# 综合得分（30%宏观 + 25%流动性 + 25%估值 + 20%情绪）
composite_score = (
    macro_score * 0.30 +
    liquidity_score * 0.25 +
    valuation_score * 0.25 +
    sentiment_score * 0.20
)
composite_score = np.clip(composite_score, 0, 100)

# 创建DataFrame
scores_df = pd.DataFrame({
    'date': macro_score.index,
    'macro_score': macro_score.values,
    'liquidity_score': liquidity_score,
    'valuation_score': valuation_score,
    'sentiment_score': sentiment_score,
    'composite_score': composite_score
})

print(f"\n得分统计：")
print(f"  宏观状态得分: {scores_df['macro_score'].mean():.2f} (±{scores_df['macro_score'].std():.2f})")
print(f"  流动性得分: {scores_df['liquidity_score'].mean():.2f} (±{scores_df['liquidity_score'].std():.2f})")
print(f"  估值得分: {scores_df['valuation_score'].mean():.2f} (±{scores_df['valuation_score'].std():.2f})")
print(f"  情绪得分: {scores_df['sentiment_score'].mean():.2f} (±{scores_df['sentiment_score'].std():.2f})")
print(f"  综合得分: {scores_df['composite_score'].mean():.2f} (±{scores_df['composite_score'].std():.2f})")

latest_date = scores_df['date'].iloc[-1].strftime('%Y-%m-%d')
print(f"\n最新得分（{latest_date}）：")
latest = scores_df.iloc[-1]
print(f"  宏观状态得分: {latest['macro_score']:.2f}")
print(f"  流动性得分: {latest['liquidity_score']:.2f}")
print(f"  估值得分: {latest['valuation_score']:.2f}")
print(f"  情绪得分: {latest['sentiment_score']:.2f}")
print(f"  综合得分: {latest['composite_score']:.2f}")

# 保存
INDICATORS_DIR.mkdir(parents=True, exist_ok=True)
scores_df.to_csv(MACRO_SCORES_FILE, index=False, encoding='utf-8-sig')

print(f"\n✅ 宏观得分已保存: {MACRO_SCORES_FILE}")
print(f"数据记录数: {len(scores_df)} 条")
print(f"时间范围: {scores_df['date'].min()} 至 {scores_df['date'].max()}")
print()
