"""
计算宏观得分数据

使用 MacroScorecard 计算四类因子得分
"""

import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.timing.macro_scorecard import MacroScorecard
from configs.data_paths import (
    REGIME_PROBS_FILE,
    M1_M2_FILE,
    HS300_FILE,
    BOND_YIELD_10Y_FILE,
    NORTHBOUND_FLOW_FILE,
    VIX_FILE,
    INDICATORS_DIR,
    MACRO_SCORES_FILE
)

print("="*80)
print("计算宏观得分数据（2016-2024）")
print("="*80)
print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# 步骤1: 加载数据
# ============================================================================
print("【步骤1】加载数据...")
print("-"*80)

# 1.1 区制概率数据
regime_probs = pd.read_csv(REGIME_PROBS_FILE)
regime_probs['date'] = pd.to_datetime(regime_probs['date'])
regime_probs = regime_probs.set_index('date').sort_index()
print(f"✅ 区制概率: {len(regime_probs)} 条记录")

# 1.2 M1/M2数据
m1_m2 = pd.read_csv(M1_M2_FILE)
m1_m2['date'] = pd.to_datetime(m1_m2['date'])
m1_m2 = m1_m2.set_index('date').sort_index()
print(f"✅ M1/M2: {len(m1_m2)} 条记录")

# 1.3 股票价格数据
hs300 = pd.read_csv(HS300_FILE)
hs300['date'] = pd.to_datetime(hs300['date'], format='%Y%m%d')  # 指定日期格式
hs300 = hs300.set_index('date').sort_index()
stock_price = hs300['close']
print(f"✅ 沪深300价格: {len(stock_price)} 条记录")

# 1.4 债券收益率数据
bond_yield = pd.read_csv(BOND_YIELD_10Y_FILE)
bond_yield['date'] = pd.to_datetime(bond_yield['date'])
bond_yield = bond_yield.set_index('date').sort_index()
bond_yield_series = bond_yield['yield']
print(f"✅ 债券收益率: {len(bond_yield_series)} 条记录")

# 1.5 北向资金流数据（可选）
try:
    northbound = pd.read_csv(NORTHBOUND_FLOW_FILE)
    northbound['date'] = pd.to_datetime(northbound['date'], format='%Y%m%d')  # YYYYMMDD格式
    northbound = northbound.set_index('date').sort_index()
    northbound_flow = northbound['northbound_flow']
    print(f"✅ 北向资金流: {len(northbound_flow)} 条记录")
except:
    northbound_flow = None
    print("⚠️ 北向资金流数据不可用")

# 1.6 VIX数据
try:
    vix = pd.read_csv(VIX_FILE)
    vix['date'] = pd.to_datetime(vix['date'])  # YYYY-MM-DD格式
    vix = vix.set_index('date').sort_index()
    vix_series = vix['vix']
    print(f"✅ VIX: {len(vix_series)} 条记录")
except:
    vix_series = None
    print("⚠️ VIX数据不可用")

print()

# ============================================================================
# 步骤2: 创建MacroScorecard并计算得分
# ============================================================================
print("【步骤2】计算宏观得分...")
print("-"*80)

scorecard = MacroScorecard()

# 2.1 宏观状态得分（基于区制概率）
print("\n1. 宏观状态得分...")
macro_score = scorecard.calculate_macro_score(regime_probs)
macro_score = pd.Series(macro_score, index=regime_probs.index)
print(f"   ✅ 有效得分: {macro_score.notna().sum()} 条")

# 2.2 流动性得分（基于M1/M2）
print("\n2. 流动性得分...")
m1_data = m1_m2['M1']
m2_data = m1_m2['M2']
liquidity_score = scorecard.calculate_liquidity_score(m1_data, m2_data)
liquidity_score = pd.Series(liquidity_score, index=m1_m2.index)
print(f"   ✅ 有效得分: {liquidity_score.notna().sum()} 条")

# 2.3 估值得分（基于股债风险溢价）
print("\n3. 估值得分...")
# 对齐股票价格和债券收益率的数据（使用交集）
common_index = stock_price.index.intersection(bond_yield_series.index)
stock_price_aligned = stock_price.loc[common_index]
bond_yield_aligned = bond_yield_series.loc[common_index]
print(f"   对齐后数据: {len(common_index)} 条记录")

valuation_score_array = scorecard.calculate_valuation_score(stock_price_aligned, bond_yield_aligned)
# 使用正确的索引
valuation_score = pd.Series(valuation_score_array, index=common_index[:len(valuation_score_array)])
print(f"   ✅ 有效得分: {valuation_score.notna().sum()} 条")

# 2.4 情绪得分（基于北向资金流、VIX）
print("\n4. 情绪得分...")
# 对齐数据
if northbound_flow is not None and vix_series is not None:
    # 使用共同的索引
    common_index_vix = northbound_flow.index.intersection(vix_series.index)
    northbound_aligned = northbound_flow.loc[common_index_vix]
    vix_aligned = vix_series.loc[common_index_vix]
    print(f"   对齐后数据: {len(common_index_vix)} 条记录")

    sentiment_score_result = scorecard.calculate_sentiment_score(
        northbound_flow=northbound_aligned,
        vix=vix_aligned
    )
    if sentiment_score_result is not None and not isinstance(sentiment_score_result, pd.Series):
        sentiment_score = pd.Series(sentiment_score_result, index=northbound_aligned.index[:len(sentiment_score_result)])
    else:
        sentiment_score = sentiment_score_result
elif northbound_flow is not None:
    sentiment_score_result = scorecard.calculate_sentiment_score(northbound_flow=northbound_flow)
    if sentiment_score_result is not None and not isinstance(sentiment_score_result, pd.Series):
        sentiment_score = pd.Series(sentiment_score_result, index=northbound_flow.index[:len(sentiment_score_result)])
    else:
        sentiment_score = sentiment_score_result
else:
    sentiment_score = None
    print(f"   ⚠️ 情绪得分不可用（缺少数据）")

if sentiment_score is not None:
    print(f"   ✅ 有效得分: {sentiment_score.notna().sum()} 条")

# 2.5 综合得分
print("\n5. 综合得分...")
composite_score = scorecard.calculate_composite_score(
    macro_score=macro_score,
    liquidity_score=liquidity_score,
    valuation_score=valuation_score,
    sentiment_score=sentiment_score
)
composite_score = pd.Series(composite_score, index=macro_score.index)
print(f"   ✅ 有效得分: {composite_score.notna().sum()} 条")

# ============================================================================
# 步骤3: 合并所有得分
# ============================================================================
print("\n【步骤3】合并所有得分...")
print("-"*80)

# 创建得分DataFrame
scores_df = pd.DataFrame({
    'date': composite_score.index,
    'macro_score': macro_score,
    'liquidity_score': liquidity_score,
    'valuation_score': valuation_score,
    'sentiment_score': sentiment_score,
    'composite_score': composite_score
})

# 前向填充缺失值
scores_df = scores_df.fillna(method='ffill').fillna(method='bfill')

# 删除仍有缺失的行
scores_df = scores_df.dropna()

print(f"✅ 最终得分数据: {len(scores_df)} 条记录")
print(f"   时间范围: {scores_df['date'].min()} 至 {scores_df['date'].max()}")

# ============================================================================
# 步骤4: 得分统计
# ============================================================================
print("\n【步骤4】得分统计...")
print("-"*80)

print("\n各得分统计（最近30天）：")
recent = scores_df.tail(30)
print(f"  宏观状态得分: {recent['macro_score'].mean():.2f}")
print(f"  流动性得分: {recent['liquidity_score'].mean():.2f}")
print(f"  估值得分: {recent['valuation_score'].mean():.2f}")
print(f"  情绪得分: {recent['sentiment_score'].mean():.2f}")
print(f"  综合得分: {recent['composite_score'].mean():.2f}")

print("\n最新得分（{}）：".format(scores_df['date'].iloc[-1].strftime('%Y-%m-%d')))
latest = scores_df.iloc[-1]
print(f"  宏观状态得分: {latest['macro_score']:.2f}")
print(f"  流动性得分: {latest['liquidity_score']:.2f}")
print(f"  估值得分: {latest['valuation_score']:.2f}")
print(f"  情绪得分: {latest['sentiment_score']:.2f}")
print(f"  综合得分: {latest['composite_score']:.2f}")

# ============================================================================
# 步骤5: 保存数据
# ============================================================================
print("\n【步骤5】保存宏观得分数据...")
print("-"*80)

# 确保输出目录存在
INDICATORS_DIR.mkdir(parents=True, exist_ok=True)

# 保存
scores_df.to_csv(MACRO_SCORES_FILE, index=False, encoding='utf-8-sig')
print(f"✅ 宏观得分已保存: {MACRO_SCORES_FILE}")

# ============================================================================
# 完成
# ============================================================================
print("\n"+"="*80)
print("✅ 宏观得分计算完成！")
print("="*80)
print(f"\n输出文件: {MACRO_SCORES_FILE}")
print(f"数据记录数: {len(scores_df)} 条")
print(f"时间范围: {scores_df['date'].min()} 至 {scores_df['date'].max()}")
print(f"\n得分范围:")
for col in ['macro_score', 'liquidity_score', 'valuation_score', 'sentiment_score', 'composite_score']:
    print(f"  {col}: {scores_df[col].min():.2f} - {scores_df[col].max():.2f}")
print()
