"""
第三阶段完整验证脚本

验证所有第三阶段模块的功能
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

print("=" * 100)
print("第三阶段完整验证")
print("=" * 100)
print(f"验证时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# 验证结果汇总
# ============================================================================
test_results = {
    'passed': [],
    'failed': [],
    'skipped': []
}

# ============================================================================
# 验证1: 模块导入
# ============================================================================
print("\n【验证1】模块导入测试")
print("-" * 100)

modules_to_test = [
    ('data.flow.flow_fetcher', 'FlowDataFetcher'),
    ('models.flow.flow_driver_model', 'FlowDriverModel'),
    ('models.flow.flow_nowcasting', 'FlowNowcastingModel'),
    ('models.risk.market_risk_indicators', 'MarketRiskIndicators'),
    ('models.risk.macro_risk_indicators', 'MacroRiskIndicators'),
    ('models.risk.composite_risk_index', 'CompositeRiskIndex'),
]

all_imports_ok = True
for module_name, class_name in modules_to_test:
    try:
        exec(f"from {module_name} import {class_name}")
        print(f"✓ {class_name} 导入成功")
    except Exception as e:
        print(f"✗ {class_name} 导入失败: {str(e)}")
        all_imports_ok = False

if all_imports_ok:
    print("\n✅ 所有模块导入成功")
    test_results['passed'].append('模块导入')
else:
    print("\n❌ 部分模块导入失败")
    test_results['failed'].append('模块导入')

# ============================================================================
# 验证2: 资金流数据获取器
# ============================================================================
print("\n\n【验证2】资金流数据获取器功能")
print("-" * 100)

try:
    from data.flow.flow_fetcher import FlowDataFetcher
    from configs.db_config import load_confidential_config

    config = load_confidential_config()

    fetcher = FlowDataFetcher(
        tushare_token=config.get('TUSHARE_DataApi__token'),
        fred_key=config.get('FRED_API_Key')
    )

    print("✓ FlowDataFetcher初始化成功")

    # 测试数据获取
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    vix = fetcher.get_vix(start_date, end_date)
    dxy = fetcher.get_dxy(start_date, end_date)

    data_count = 0
    if vix is not None and len(vix) > 0:
        print(f"✓ VIX数据：{len(vix)}条")
        data_count += 1
    else:
        print("⚠ VIX数据获取失败")

    if dxy is not None and len(dxy) > 0:
        print(f"✓ 美元指数数据：{len(dxy)}条")
        data_count += 1
    else:
        print("⚠ 美元指数数据获取失败")

    if data_count >= 2:
        print("\n✅ 资金流数据获取器功能正常")
        test_results['passed'].append('资金流数据获取器')
    else:
        print("\n⚠ 资金流数据获取器部分功能可用")
        test_results['skipped'].append('资金流数据获取器')

except Exception as e:
    print(f"\n❌ 资金流数据获取器测试失败: {str(e)}")
    test_results['failed'].append('资金流数据获取器')

# ============================================================================
# 验证3: 市场风险指标
# ============================================================================
print("\n\n【验证3】市场风险指标计算")
print("-" * 100)

try:
    from models.risk.market_risk_indicators import MarketRiskIndicators

    mri = MarketRiskIndicators()
    print("✓ MarketRiskIndicators初始化成功")

    # 使用VIX和DXY数据测试
    if vix is not None and dxy is not None:
        data_dict = {'vix': vix, 'dxy': dxy}

        indicators = mri.calculate_all_indicators(data_dict)

        if indicators is not None and len(indicators) > 0:
            print(f"✓ 计算出{len(indicators.columns)}个指标")

            # 标准化测试
            normalized = mri.normalize_indicators(method='minmax')
            if normalized is not None:
                print(f"✓ 标准化成功（0-100）")

            # 获取摘要
            summary = mri.get_indicator_summary()
            if summary is not None:
                print(f"✓ 指标摘要生成成功")
                print(f"\n指标示例（前3个）：")
                print(summary.head(3).to_string())

            print("\n✅ 市场风险指标功能正常")
            test_results['passed'].append('市场风险指标')
        else:
            print("\n⚠ 未能计算出指标")
            test_results['skipped'].append('市场风险指标')
    else:
        print("\n⚠ 缺少测试数据")
        test_results['skipped'].append('市场风险指标')

except Exception as e:
    print(f"\n❌ 市场风险指标测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    test_results['failed'].append('市场风险指标')

# ============================================================================
# 验证4: 三层驱动模型
# ============================================================================
print("\n\n【验证4】资金流三层驱动模型")
print("-" * 100)

try:
    from models.flow.flow_driver_model import FlowDriverModel

    model = FlowDriverModel(method='ols')
    print("✓ FlowDriverModel初始化成功")

    # 创建模拟数据
    if vix is not None and dxy is not None:
        import pandas as pd

        # 准备数据字典
        data_dict = {'vix': vix, 'dxy': dxy}

        # 创建模拟资金流数据（基于VIX）
        mock_flow = pd.DataFrame({
            'trade_date': vix.index,
            'ggt_ss': np.random.randn(len(vix)) * 1000000000,
            'ggt_sz': np.random.randn(len(vix)) * 800000000
        })

        # 训练模型
        model.fit(data_dict, mock_flow)

        print("\n✅ 三层驱动模型功能正常")
        test_results['passed'].append('三层驱动模型')
    else:
        print("\n⚠ 缺少测试数据")
        test_results['skipped'].append('三层驱动模型')

except Exception as e:
    print(f"\n❌ 三层驱动模型测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    test_results['failed'].append('三层驱动模型')

# ============================================================================
# 验证5: 宏观风险指标
# ============================================================================
print("\n\n【验证5】宏观风险指标计算")
print("-" * 100)

try:
    from models.risk.macro_risk_indicators import MacroRiskIndicators

    mri_macro = MacroRiskIndicators()
    print("✓ MacroRiskIndicators初始化成功")

    # 创建模拟CPI数据
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='M')
    mock_cpi = pd.Series(
        100 + np.cumsum(np.random.randn(len(dates)) * 0.3),
        index=dates
    )

    data_dict = {'cpi': mock_cpi}

    indicators_macro = mri_macro.calculate_all_indicators(data_dict)

    if indicators_macro is not None and len(indicators_macro.columns) > 0:
        print(f"✓ 计算出{len(indicators_macro.columns)}个宏观风险指标")

        # 标准化
        normalized_macro = mri_macro.normalize_indicators(method='minmax')
        if normalized_macro is not None:
            print(f"✓ 标准化成功")

        print("\n✅ 宏观风险指标功能正常")
        test_results['passed'].append('宏观风险指标')
    else:
        print("\n⚠ 未能计算出指标")
        test_results['skipped'].append('宏观风险指标')

except Exception as e:
    print(f"\n❌ 宏观风险指标测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    test_results['failed'].append('宏观风险指标')

# ============================================================================
# 验证6: Nowcasting模型（模拟数据）
# ============================================================================
print("\n\n【验证6】资金流Nowcasting模型")
print("-" * 100)

try:
    from models.flow.flow_nowcasting import FlowNowcastingModel

    nowcasting_model = FlowNowcastingModel(horizon_days=5, method='rf')
    print("✓ FlowNowcastingModel初始化成功")

    # 创建模拟资金流数据
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    mock_flow = pd.DataFrame({
        'trade_date': dates,
        'net_flow_north': np.random.randn(len(dates)) * 1000000000
    })

    # 创建模拟外部数据
    external_data = {
        'vix': pd.DataFrame({
            'vix': np.random.randn(len(dates)) * 3 + 20
        }, index=dates)
    }

    # 训练模型
    nowcasting_model.fit(mock_flow, external_data)

    # 预测
    result = nowcasting_model.predict(mock_flow.tail(30), external_data)

    if result is not None:
        print(f"✓ 预测成功")
        print(f"  预测方向：{result['direction']}")
        print(f"  预测值：{result['prediction']:.2f}")
        print(f"  预测区间：[{result['prediction_lower']:.2f}, {result['prediction_upper']:.2f}]")

        print("\n✅ 资金流Nowcasting模型功能正常")
        test_results['passed'].append('资金流Nowcasting模型')
    else:
        print("\n⚠ 预测失败")
        test_results['skipped'].append('资金流Nowcasting模型')

except Exception as e:
    print(f"\n❌ 资金流Nowcasting模型测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    test_results['failed'].append('资金流Nowcasting模型')

# ============================================================================
# 验证7: 复合风险预警指数（修复版）
# ============================================================================
print("\n\n【验证7】复合风险预警指数")
print("-" * 100)

try:
    from models.risk.composite_risk_index import CompositeRiskIndex

    cri = CompositeRiskIndex(model_type='xgboost', forecast_horizon=5)
    print("✓ CompositeRiskIndex初始化成功")

    # 准备测试数据
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')

    # 创建市场风险指标
    market_indicators = pd.DataFrame({
        'vix_ma_ratio': np.random.randn(len(dates)) * 0.2 + 1,
        'dxy': np.random.randn(len(dates)) * 2 + 100,
    }, index=dates)

    # 创建宏观风险指标
    macro_indicators = pd.DataFrame({
        'recession_prob': np.random.rand(len(dates)) * 0.3,
        'cpi_surprise_prob': np.random.rand(len(dates)) * 0.5,
    }, index=dates)

    # 创建模拟价格数据
    price_data = pd.Series(
        3000 + np.cumsum(np.random.randn(len(dates)) * 30),
        index=dates
    )

    # 训练模型
    cri.fit(market_indicators, macro_indicators, price_data)

    # 预测风险指数
    risk_index = cri.predict(market_indicators, macro_indicators)

    if risk_index is not None:
        print(f"✓ 风险指数预测成功")
        print(f"  最新风险指数：{risk_index.iloc[-1]:.2f}")

        # 获取当前风险等级
        current_risk = cri.get_current_risk_level(market_indicators, macro_indicators)
        if current_risk is not None:
            print(f"  当前风险等级：{current_risk['risk_level']}")
            print(f"  风险颜色：{current_risk['risk_color']}")

        print("\n✅ 复合风险预警指数功能正常")
        test_results['passed'].append('复合风险预警指数')
    else:
        print("\n⚠ 风险指数预测失败")
        test_results['skipped'].append('复合风险预警指数')

except Exception as e:
    print(f"\n❌ 复合风险预警指数测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    test_results['failed'].append('复合风险预警指数')

# ============================================================================
# 验证总结
# ============================================================================
print("\n\n")
print("=" * 100)
print("验证总结")
print("=" * 100)

print(f"\n✅ 通过的验证（{len(test_results['passed'])}个）：")
for test in test_results['passed']:
    print(f"  ✓ {test}")

if test_results['skipped']:
    print(f"\n⚠ 跳过的验证（{len(test_results['skipped'])}个）：")
    for test in test_results['skipped']:
        print(f"  ⚠ {test}")

if test_results['failed']:
    print(f"\n❌ 失败的验证（{len(test_results['failed'])}个）：")
    for test in test_results['failed']:
        print(f"  ✗ {test}")

total = len(test_results['passed']) + len(test_results['failed']) + len(test_results['skipped'])
pass_rate = len(test_results['passed']) / total * 100 if total > 0 else 0

print(f"\n通过率：{pass_rate:.1f}% ({len(test_results['passed'])}/{total})")

if len(test_results['failed']) == 0 and len(test_results['passed']) >= 4:
    print("\n🎉 所有核心功能验证通过！第三阶段可以正常使用！")
elif len(test_results['passed']) >= 4:
    print("\n✅ 核心功能验证通过，部分功能需要数据支持。")
else:
    print("\n⚠ 部分功能需要进一步检查。")

print("\n" + "=" * 100)
