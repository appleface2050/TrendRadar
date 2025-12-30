"""
重新生成风险指数数据（修复日期格式）
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs.data_paths import (
    HS300_FILE,
    VIX_FILE,
    RISK_INDEX_FILE
)

print("修复风险指数日期格式...")

# 加载数据并修复日期格式
hs300 = pd.read_csv(HS300_FILE)
hs300['date'] = pd.to_datetime(hs300['date'], format='%Y%m%d')  # 确保正确解析
hs300 = hs300.set_index('date').sort_index()

vix = pd.read_csv(VIX_FILE)
vix['date'] = pd.to_datetime(vix['date'])
vix = vix.set_index('date').sort_index()

print(f"沪深300: {len(hs300)} 条, 日期范围: {hs300.index.min()} 至 {hs300.index.max()}")
print(f"VIX: {len(vix)} 条, 日期范围: {vix.index.min()} 至 {vix.index.max()}")

# 计算收益率
hs300['returns'] = hs300['close'].pct_change()
hs300['returns_vol_20d'] = hs300['returns'].rolling(window=20).std()

hs300['rolling_max'] = hs300['close'].rolling(window=252, min_periods=1).max()
hs300['drawdown'] = (hs300['close'] - hs300['rolling_max']) / hs300['rolling_max']
hs300['max_drawdown_20d'] = hs300['drawdown'].rolling(window=20).min()

# VIX标准化
vix_normalized = (vix['vix'] - vix['vix'].rolling(252).mean()) / vix['vix'].rolling(252).std()

# 合并
risk_indicators = pd.DataFrame(index=hs300.index)
risk_indicators['volatility'] = hs300['returns_vol_20d']
risk_indicators['drawdown'] = -hs300['max_drawdown_20d']
risk_indicators = risk_indicators.join(vix_normalized, how='left', rsuffix='_vix')

# 填充缺失值
risk_indicators = risk_indicators.fillna(method='ffill').fillna(method='bfill')

# 计算风险指数
risk_index_raw = risk_indicators.mean(axis=1)
rolling_median = risk_index_raw.rolling(window=252, min_periods=60).median()
rolling_std = risk_index_raw.rolling(window=252, min_periods=60).std()
risk_index_z = (risk_index_raw - rolling_median) / rolling_std
risk_index = 100 * stats.norm.cdf(risk_index_z)

# 转换为Series
risk_index = pd.Series(risk_index, index=risk_index_z.index).dropna()

# 保存（确保日期格式正确）
risk_df = pd.DataFrame({
    'date': risk_index.index.strftime('%Y-%m-%d'),  # 格式化为字符串
    'risk_index': risk_index.values
})
risk_df.to_csv(RISK_INDEX_FILE, index=False, encoding='utf-8-sig')

print(f"\n✅ 风险指数已重新生成: {RISK_INDEX_FILE}")
print(f"数据记录数: {len(risk_df)} 条")
print(f"日期格式: {risk_df['date'].iloc[0]} (类型: {type(risk_df['date'].iloc[0])})")
print(f"时间范围: {risk_df['date'].min()} 至 {risk_df['date'].max()}")
