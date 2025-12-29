"""
生成复合风险指数数据

基于市场风险指标生成复合风险指数（0-100）
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

from configs.data_paths import (
    VIX_FILE,
    NORTHBOUND_FLOW_FILE,
    HS300_FILE,
    INDICATORS_DIR,
    RISK_INDEX_FILE
)

print("="*80)
print("生成复合风险指数数据（2016-2024）")
print("="*80)
print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# 步骤1: 加载市场数据
# ============================================================================
print("【步骤1】加载市场数据...")
print("-"*80)

# 加载沪深300价格数据
hs300 = pd.read_csv(HS300_FILE)
hs300['date'] = pd.to_datetime(hs300['date'])
hs300 = hs300.set_index('date').sort_index()
print(f"✅ 沪深300: {len(hs300)} 条记录")

# 加载VIX数据
vix = pd.read_csv(VIX_FILE)
vix['date'] = pd.to_datetime(vix['date'])
vix = vix.set_index('date').sort_index()
print(f"✅ VIX: {len(vix)} 条记录")

# 加载北向资金流数据
try:
    northbound = pd.read_csv(NORTHBOUND_FLOW_FILE)
    northbound['date'] = pd.to_datetime(northbound['date'])
    northbound = northbound.set_index('date').sort_index()
    print(f"✅ 北向资金流: {len(northbound)} 条记录")
except:
    northbound = None
    print("⚠️ 北向资金流数据不可用")

# ============================================================================
# 步骤2: 计算市场风险指标
# ============================================================================
print("\n【步骤2】计算市场风险指标...")
print("-"*80)

# 2.1 计算沪深300收益率
hs300['returns'] = hs300['close'].pct_change()
hs300['returns_vol_20d'] = hs300['returns'].rolling(window=20).std()

# 2.2 计算最大回撤
hs300['rolling_max'] = hs300['close'].rolling(window=252, min_periods=1).max()
hs300['drawdown'] = (hs300['close'] - hs300['rolling_max']) / hs300['rolling_max']
hs300['max_drawdown_20d'] = hs300['drawdown'].rolling(window=20).min()

# 2.3 VIX（已归一化）
vix_normalized = (vix['vix'] - vix['vix'].rolling(252).mean()) / vix['vix'].rolling(252).std()

# 2.4 北向资金流（如果有）
if northbound is not None:
    # 计算资金流变化率的绝对值（越大表示波动越大）
    northbound['flow_change'] = northbound['northbound_flow'].diff().abs()
    northbound['flow_vol_20d'] = northbound['flow_change'].rolling(window=20).std()
    northbound_normalized = (northbound['flow_vol_20d'] - northbound['flow_vol_20d'].rolling(252).mean()) / northbound['flow_vol_20d'].rolling(252).std()
else:
    northbound_normalized = None

print("✅ 市场风险指标计算完成")

# ============================================================================
# 步骤3: 合并指标
# ============================================================================
print("\n【步骤3】合并风险指标...")
print("-"*80)

# 创建风险指标DataFrame
risk_indicators = pd.DataFrame(index=hs300.index)
risk_indicators['volatility'] = hs300['returns_vol_20d']
risk_indicators['drawdown'] = -hs300['max_drawdown_20d']  # 取负值，回撤越大风险越高

# 合并VIX数据
risk_indicators = risk_indicators.join(vix_normalized, how='left', rsuffix='_vix')

if northbound_normalized is not None:
    risk_indicators = risk_indicators.join(northbound_normalized, how='left', rsuffix='_flow')

# 只保留有数据的列
available_cols = [col for col in risk_indicators.columns if risk_indicators[col].notna().sum() > 0]
risk_indicators = risk_indicators[available_cols]

print(f"可用指标: {list(risk_indicators.columns)}")

# 简单前向填充缺失值
risk_indicators = risk_indicators.fillna(method='ffill').fillna(method='bfill')

print(f"✅ 有效数据: {len(risk_indicators)} 条记录")
print(f"   时间范围: {risk_indicators.index.min()} 至 {risk_indicators.index.max()}")

# ============================================================================
# 步骤4: 计算复合风险指数
# ============================================================================
print("\n【步骤4】计算复合风险指数...")
print("-"*80)

# 标准化每个指标（z-score）
risk_indicators_std = (risk_indicators - risk_indicators.mean()) / risk_indicators.std()

# 计算等权平均值
risk_index_raw = risk_indicators_std.mean(axis=1)

# 转换为0-100分制（使用历史分位数）
# 0分 = 最低风险，100分 = 最高风险
rolling_median = risk_index_raw.rolling(window=252, min_periods=60).median()
rolling_std = risk_index_raw.rolling(window=252, min_periods=60).std()

# 计算z-score相对滚动统计量
risk_index_z = (risk_index_raw - rolling_median) / rolling_std

# 转换为0-100分（使用累积分布函数）
from scipy import stats
risk_index = 100 * stats.norm.cdf(risk_index_z)

# 转换为Series并删除缺失值
risk_index = pd.Series(risk_index, index=risk_index_z.index).dropna()
print(f"✅ 复合风险指数: {len(risk_index)} 条记录")
print(f"   时间范围: {risk_index.index.min()} 至 {risk_index.index.max()}")

# ============================================================================
# 步骤5: 风险等级统计
# ============================================================================
print("\n【步骤5】风险等级统计...")
print("-"*80)

# 定义风险等级
def get_risk_level(score):
    if score < 20:
        return '低风险'
    elif score < 40:
        return '偏低风险'
    elif score < 60:
        return '中等风险'
    elif score < 80:
        return '较高风险'
    else:
        return '高风险'

risk_levels = risk_index.apply(get_risk_level)
level_counts = risk_levels.value_counts().sort_index()

print("\n风险等级分布：")
for level, count in level_counts.items():
    pct = count / len(risk_index) * 100
    print(f"  {level}: {count} 天 ({pct:.1f}%)")

# ============================================================================
# 步骤6: 保存数据
# ============================================================================
print("\n【步骤6】保存复合风险指数...")
print("-"*80)

# 确保输出目录存在
INDICATORS_DIR.mkdir(parents=True, exist_ok=True)

# 保存为DataFrame
risk_df = pd.DataFrame({
    'date': risk_index.index,
    'risk_index': risk_index.values
})
risk_df.to_csv(RISK_INDEX_FILE, index=False, encoding='utf-8-sig')
print(f"✅ 复合风险指数已保存: {RISK_INDEX_FILE}")

# ============================================================================
# 步骤7: 当前风险状态
# ============================================================================
print("\n【步骤7】当前风险状态...")
print("-"*80)

latest_risk = risk_index.iloc[-1]
latest_level = get_risk_level(latest_risk)
latest_date = risk_index.index[-1].strftime('%Y-%m-%d')

print(f"\n最新风险指数（{latest_date}）")
print(f"  风险指数: {latest_risk:.2f}")
print(f"  风险等级: {latest_level}")

# 计算近30天平均
recent_avg = risk_index.tail(30).mean()
recent_level = get_risk_level(recent_avg)
print(f"\n近30天平均")
print(f"  风险指数: {recent_avg:.2f}")
print(f"  风险等级: {recent_level}")

# ============================================================================
# 完成
# ============================================================================
print("\n"+"="*80)
print("✅ 复合风险指数生成完成！")
print("="*80)
print(f"\n输出文件: {RISK_INDEX_FILE}")
print(f"数据记录数: {len(risk_df)} 条")
print(f"时间范围: {risk_df['date'].min()} 至 {risk_df['date'].max()}")
print()
