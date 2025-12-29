"""
生成区制概率数据

使用第二阶段的区制模型生成 2016-2024 的区制概率数据
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

from models.regime.cn_regime import CNPolicyRegimeModel
from configs.data_paths import INDICATORS_DIR, REGIME_PROBS_FILE

print("="*80)
print("生成中国区制概率数据（2016-2024）")
print("="*80)
print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# 步骤1: 加载指标数据
# ============================================================================
print("【步骤1】加载历史指标数据...")
print("-"*80)

input_file = '../data/temp/cn_indicators_for_regime.csv'
df = pd.read_csv(input_file)
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date').sort_index()

print(f"✅ 原始数据: {len(df)} 条记录")
print(f"   时间范围: {df.index.min()} 至 {df.index.max()}")

# 筛选 2016 年以后的数据
df_recent = df[df.index >= '2016-01-01'].copy()
print(f"✅ 2016年后数据: {len(df_recent)} 条记录")
print(f"   时间范围: {df_recent.index.min()} 至 {df_recent.index.max()}")

# ============================================================================
# 步骤2: 数据预处理和因子提取
# ============================================================================
print("\n【步骤2】提取宏观因子...")
print("-"*80)

# 使用简化方法提取因子（基于已有指标）
# 1. 增长因子：GDP（季度）和 PMI（月度）
growth_indicator = df_recent['PMI'].copy()

# 2. 通胀因子：CPI同比
inflation_indicator = df_recent['CPI_YOY'].copy()

# 3. 流动性因子：M2同比增速
m2_yoy = df_recent['M2'].pct_change(periods=12) * 100
liquidity_indicator = m2_yoy

# 对齐数据
factors_df = pd.DataFrame({
    'growth': growth_indicator,
    'inflation': inflation_indicator,
    'liquidity': liquidity_indicator
})

# 删除缺失值
factors_df = factors_df.dropna()
print(f"✅ 有效数据: {len(factors_df)} 条记录")
print(f"   时间范围: {factors_df.index.min()} 至 {factors_df.index.max()}")

# 标准化因子
factors_standardized = (factors_df - factors_df.mean()) / factors_df.std()

print("\n因子统计：")
print(factors_standardized.describe())

# ============================================================================
# 步骤3: 训练区制模型
# ============================================================================
print("\n【步骤3】训练马尔可夫区制转移模型...")
print("-"*80)

# 创建区制模型
regime_model = CNPolicyRegimeModel(n_regimes=4)

# 拟合模型
regime_model.fit_with_factors(
    growth_factor=factors_standardized['growth'],
    inflation_factor=factors_standardized['inflation'],
    liquidity_factor=factors_standardized['liquidity']
)

print("✅ 区制模型训练完成")

# ============================================================================
# 步骤4: 生成区制概率
# ============================================================================
print("\n【步骤4】生成区制概率...")
print("-"*80)

regime_probs = regime_model.get_regime_probs()
print(f"✅ 区制概率数据: {len(regime_probs)} 条记录")
print(f"   时间范围: {regime_probs.index.min()} 至 {regime_probs.index.max()}")

# ============================================================================
# 步骤5: 扩展到日度频率（用于回测）
# ============================================================================
print("\n【步骤5】扩展到日度频率...")
print("-"*80)

# 重采样到日度（前向填充）
regime_probs_daily = regime_probs.resample('D').ffill()
print(f"✅ 日度数据: {len(regime_probs_daily)} 条记录")
print(f"   时间范围: {regime_probs_daily.index.min()} 至 {regime_probs_daily.index.max()}")

# ============================================================================
# 步骤6: 保存数据
# ============================================================================
print("\n【步骤6】保存区制概率数据...")
print("-"*80)

# 确保输出目录存在
INDICATORS_DIR.mkdir(parents=True, exist_ok=True)

# 保存月度数据
output_file_monthly = INDICATORS_DIR / 'regime_probabilities_monthly.csv'
regime_probs.to_csv(output_file_monthly, encoding='utf-8-sig')
print(f"✅ 月度数据已保存: {output_file_monthly}")

# 保存日度数据
output_file_daily = INDICATORS_DIR / 'regime_probabilities.csv'
regime_probs_daily.to_csv(output_file_daily, encoding='utf-8-sig')
print(f"✅ 日度数据已保存: {output_file_daily}")

# ============================================================================
# 步骤7: 数据统计
# ============================================================================
print("\n【步骤7】区制概率统计...")
print("-"*80)

print("\n各区制出现频率：")
for col in regime_probs_daily.columns:
    count = (regime_probs_daily[col] > 0.5).sum()
    pct = count / len(regime_probs_daily) * 100
    print(f"  {col}: {count} 天 ({pct:.1f}%)")

print("\n当前区制（最新）：")
latest = regime_probs_daily.iloc[-1]
print(f"  日期: {regime_probs_daily.index[-1].strftime('%Y-%m-%d')}")
for col, prob in latest.items():
    regime_name = CNPolicyRegimeModel.REGIME_NAMES.get(col, col)
    print(f"  {col} ({regime_name}): {prob:.2%}")

# ============================================================================
# 完成
# ============================================================================
print("\n"+"="*80)
print("✅ 区制概率数据生成完成！")
print("="*80)
print(f"\n输出文件：")
print(f"  月度: {output_file_monthly}")
print(f"  日度: {output_file_daily}")
print(f"\n数据记录数: {len(regime_probs_daily)} 条")
print(f"时间范围: {regime_probs_daily.index.min()} 至 {regime_probs_daily.index.max()}")
print()
