"""
运行宏观策略回测

验证策略在2016-2024年的表现
"""

import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.runner.backtest_engine import BacktestEngine
from configs.data_paths import (
    HS300_FILE,
    MACRO_SCORES_FILE,
    RISK_INDEX_FILE
)

print("="*80)
print("宏观策略回测（2016-2024）")
print("="*80)
print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# 步骤1: 加载数据
# ============================================================================
print("【步骤1】加载数据...")
print("-"*80)

# 1.1 价格数据
print("\n1. 加载价格数据...")
hs300 = pd.read_csv(HS300_FILE)
hs300['date'] = pd.to_datetime(hs300['date'], format='%Y%m%d')
hs300 = hs300.set_index('date').sort_index()
print(f"   沪深300: {len(hs300)} 条记录")
print(f"   时间范围: {hs300.index.min()} 至 {hs300.index.max()}")

# 1.2 宏观得分数据
print("\n2. 加载宏观得分...")
macro_scores = pd.read_csv(MACRO_SCORES_FILE)
macro_scores['date'] = pd.to_datetime(macro_scores['date'])
macro_scores = macro_scores.set_index('date').sort_index()
print(f"   宏观得分: {len(macro_scores)} 条记录")
print(f"   时间范围: {macro_scores.index.min()} 至 {macro_scores.index.max()}")

# 1.3 风险指数数据
print("\n3. 加载风险指数...")
risk_index = pd.read_csv(RISK_INDEX_FILE)
risk_index['date'] = pd.to_datetime(risk_index['date'])
risk_index = risk_index.set_index('date').sort_index()
print(f"   风险指数: {len(risk_index)} 条记录")
print(f"   时间范围: {risk_index.index.min()} 至 {risk_index.index.max()}")

print()

# ============================================================================
# 步骤2: 数据对齐
# ============================================================================
print("【步骤2】数据对齐...")
print("-"*80)

# 找到共同的日期范围
start_date = max(hs300.index.min(), macro_scores.index.min(), risk_index.index.min())
end_date = min(hs300.index.max(), macro_scores.index.max(), risk_index.index.max())

print(f"\n回测期间: {start_date} 至 {end_date}")

# 筛选数据
hs300_bt = hs300.loc[start_date:end_date]
macro_scores_bt = macro_scores.loc[start_date:end_date]
risk_index_bt = risk_index.loc[start_date:end_date]

print(f"\n对齐后数据量:")
print(f"  价格数据: {len(hs300_bt)} 条")
print(f"  宏观得分: {len(macro_scores_bt)} 条")
print(f"  风险指数: {len(risk_index_bt)} 条")

# 前向填充缺失值
macro_scores_bt = macro_scores_bt.fillna(method='ffill').fillna(method='bfill')
risk_index_bt = risk_index_bt.fillna(method='ffill').fillna(method='bfill')

# ============================================================================
# 步骤3: 准备回测数据文件
# ============================================================================
print("\n【步骤3】准备回测数据...")
print("-"*80)

# 创建临时目录
import tempfile
temp_dir = tempfile.mkdtemp()
print(f"\n临时目录: {temp_dir}")

# 保存价格数据
price_file = os.path.join(temp_dir, 'hs300.csv')
hs300_bt.to_csv(price_file)
print(f"✅ 价格数据: {price_file}")

# 保存宏观得分数据（只保留综合得分）
macro_file = os.path.join(temp_dir, 'macro_scores.csv')
macro_simple = pd.DataFrame({
    'date': macro_scores_bt.index,
    'composite_score': macro_scores_bt['composite_score']
})
macro_simple.to_csv(macro_file, index=False)
print(f"✅ 宏观得分: {macro_file}")

# 保存风险指数
risk_file = os.path.join(temp_dir, 'risk_index.csv')
risk_simple = pd.DataFrame({
    'date': risk_index_bt.index,
    'risk_index': risk_index_bt['risk_index']
})
risk_simple.to_csv(risk_file, index=False)
print(f"✅ 风险指数: {risk_file}")

# ============================================================================
# 步骤4: 运行回测
# ============================================================================
print("\n【步骤4】运行回测...")
print("-"*80)

try:
    engine = BacktestEngine(
        initial_cash=1000000.0,
        commission=0.001,
        slippage=0.001
    )

    # 运行回测
    results = engine.run_backtest(
        price_file=price_file,
        macro_file=macro_file,
        risk_file=risk_file,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )

    print("\n✅ 回测完成！")

except Exception as e:
    print(f"\n❌ 回测失败: {str(e)}")
    import traceback
    traceback.print_exc()

    # 简化版回测（手动计算）
    print("\n运行简化版回测...")
    print("-"*80)

    # 对齐数据到交易日
    common_index = hs300_bt.index.intersection(macro_scores_bt.index)
    hs300_aligned = hs300_bt.loc[common_index]
    scores_aligned = macro_scores_bt.loc[common_index]
    risk_aligned = risk_index_bt.loc[common_index]

    print(f"有效交易日: {len(common_index)} 天")

    # 计算信号（基于综合得分）
    # 得分 > 60: 100%仓位
    # 得分 40-60: 50%仓位
    # 得分 < 40: 0%仓位
    def get_position(score):
        if score > 60:
            return 1.0
        elif score > 40:
            return 0.5
        else:
            return 0.0

    signals = scores_aligned['composite_score'].apply(get_position)

    # 计算收益率
    hs300_returns = hs300_aligned['close'].pct_change()

    # 策略收益率
    strategy_returns = signals.shift(1) * hs300_returns  # 使用前一日的信号

    # 计算累计收益
    initial_value = 1000000.0
    strategy_cumulative = (1 + strategy_returns.fillna(0)).cumprod() * initial_value
    benchmark_cumulative = (1 + hs300_returns.fillna(0)).cumprod() * initial_value

    # 计算最终价值
    strategy_final = strategy_cumulative.iloc[-1]
    benchmark_final = benchmark_cumulative.iloc[-1]

    strategy_return = (strategy_final / initial_value - 1) * 100
    benchmark_return = (benchmark_final / initial_value - 1) * 100

    print(f"\n回测结果:")
    print(f"  策略最终资产: ¥{strategy_final:,.2f}")
    print(f"  基准最终资产: ¥{benchmark_final:,.2f}")
    print(f"  策略收益率: {strategy_return:.2f}%")
    print(f"  基准收益率: {benchmark_return:.2f}%")
    print(f"  超额收益: {strategy_return - benchmark_return:.2f}%")

    # 计算最大回撤
    def calculate_max_drawdown(cumulative_returns):
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        return drawdown.min()

    strategy_max_dd = calculate_max_drawdown(strategy_cumulative)
    benchmark_max_dd = calculate_max_drawdown(benchmark_cumulative)

    print(f"\n风险指标:")
    print(f"  策略最大回撤: {strategy_max_dd*100:.2f}%")
    print(f"  基准最大回撤: {benchmark_max_dd*100:.2f}%")

    # 计算夏普比率
    strategy_sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
    benchmark_sharpe = hs300_returns.mean() / hs300_returns.std() * np.sqrt(252)

    print(f"\n夏普比率:")
    print(f"  策略夏普比率: {strategy_sharpe:.2f}")
    print(f"  基准夏普比率: {benchmark_sharpe:.2f}")

    # 胜率
    winning_days = (strategy_returns > 0).sum()
    total_days = strategy_returns.notna().sum()
    win_rate = winning_days / total_days * 100

    print(f"\n交易统计:")
    print(f"  胜率: {win_rate:.2f}%")
    print(f"  交易天数: {total_days}")

    print()
    print("="*80)
    print("✅ 回测完成！")
    print("="*80)

    # 清理临时文件
    import shutil
    shutil.rmtree(temp_dir)
    print(f"\n临时文件已清理")
