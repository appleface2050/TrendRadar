"""
第四阶段模块测试脚本

验证所有模块是否正常工作

运行方式：
python scripts/test_all_modules.py
"""

import sys
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("第四阶段模块测试")
print("=" * 80)
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 测试结果
test_results = {}


def test_imports():
    """测试模块导入"""
    print("1. 测试模块导入...")
    print("-" * 80)

    modules_to_test = [
        ('多因子打分系统', 'strategies.timing.macro_scorecard'),
        ('信号生成器', 'strategies.timing.signal_generator'),
        ('自定义数据源', 'backtest.aligner.macro_data_feed'),
        ('Backtrader策略', 'backtest.strategies.macro_strategy'),
        ('回测引擎', 'backtest.runner.backtest_engine'),
        ('绩效归因', 'backtest.analysis.performance_attribution'),
        ('报告生成器', 'backtest.analysis.report_generator'),
        ('行业轮动模型', 'strategies.rotation.industry_macro_db'),
        ('行业选择器', 'strategies.rotation.industry_selector'),
    ]

    for name, module_path in modules_to_test:
        try:
            __import__(module_path)
            print(f"  ✅ {name}")
            test_results[name] = True
        except Exception as e:
            print(f"  ❌ {name}: {str(e)}")
            test_results[name] = False

    print()


def test_macro_scorecard():
    """测试多因子打分系统"""
    print("2. 测试多因子打分系统...")
    print("-" * 80)

    try:
        import pandas as pd
        import numpy as np
        from strategies.timing.macro_scorecard import MacroScorecard

        # 创建模拟数据
        dates = pd.date_range('2020-01-01', periods=100, freq='D')

        # 区制概率
        regime_probs = pd.DataFrame({
            'Regime_1': np.random.uniform(0.2, 0.5, 100),
            'Regime_2': np.random.uniform(0.1, 0.3, 100),
            'Regime_3': np.random.uniform(0.1, 0.3, 100),
            'Regime_4': np.random.uniform(0.05, 0.2, 100)
        }, index=dates)

        # M1、M2数据
        m1_data = pd.Series(np.random.uniform(5, 15, 100), index=dates)
        m2_data = pd.Series(np.random.uniform(8, 12, 100), index=dates)

        # 价格和利率
        stock_price = pd.Series(3000 + np.cumsum(np.random.randn(100) * 10), index=dates)
        bond_yield = pd.Series(0.03 + np.random.randn(100) * 0.01, index=dates)

        # 资金流
        northbound_flow = pd.Series(np.random.randn(100) * 50, index=dates)

        # 计算得分
        scorecard = MacroScorecard()
        macro_score = scorecard.calculate_macro_score(regime_probs)
        liquidity_score = scorecard.calculate_liquidity_score(m1_data, m2_data)
        valuation_score = scorecard.calculate_valuation_score(stock_price, bond_yield)
        sentiment_score = scorecard.calculate_sentiment_score(northbound_flow)
        composite_score = scorecard.calculate_composite_score(
            macro_score, liquidity_score, valuation_score, sentiment_score
        )

        print(f"  ✅ 宏观得分计算成功")
        print(f"     - 宏观状态得分: {macro_score.iloc[-1]:.2f}")
        print(f"     - 流动性得分: {liquidity_score.iloc[-1]:.2f}")
        print(f"     - 估值得分: {valuation_score.iloc[-1]:.2f}")
        print(f"     - 情绪得分: {sentiment_score.iloc[-1]:.2f}")
        print(f"     - 综合得分: {composite_score.iloc[-1]:.2f}")

        test_results['多因子打分系统_功能'] = True

    except Exception as e:
        print(f"  ❌ 测试失败: {str(e)}")
        test_results['多因子打分系统_功能'] = False

    print()


def test_signal_generator():
    """测试信号生成器"""
    print("3. 测试信号生成器...")
    print("-" * 80)

    try:
        import pandas as pd
        import numpy as np
        from strategies.timing.signal_generator import SignalGenerator

        # 创建模拟综合得分
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        composite_score = pd.Series(np.random.uniform(20, 80, 100), index=dates)
        risk_index = pd.Series(np.random.uniform(10, 60, 100), index=dates)

        # 生成信号
        generator = SignalGenerator(risk_adjustment=True)
        results = generator.generate_all(
            composite_score=composite_score,
            risk_index=risk_index
        )

        print(f"  ✅ 信号生成成功")
        print(f"     - 当前仓位: {results['risk_adjusted_position'].iloc[-1]:.2%}")
        print(f"     - 当前信号: {results['signals'].iloc[-1]}")

        test_results['信号生成器_功能'] = True

    except Exception as e:
        print(f"  ❌ 测试失败: {str(e)}")
        test_results['信号生成器_功能'] = False

    print()


def test_industry_rotation():
    """测试行业轮动"""
    print("4. 测试行业轮动模块...")
    print("-" * 80)

    try:
        import pandas as pd
        import numpy as np
        from strategies.rotation.industry_macro_db import IndustryMacroDB
        from strategies.rotation.industry_selector import IndustrySelector

        # 创建模拟数据
        dates = pd.date_range('2020-01-01', periods=100, freq='D')

        # 区制序列
        regime_sequence = pd.Series(
            np.random.choice(['Regime_1', 'Regime_2', 'Regime_3', 'Regime_4'], 100),
            index=dates
        )

        # 行业价格
        industry_prices = {}
        for industry in ['金融', '科技', '消费']:
            prices = 100 + np.cumsum(np.random.randn(100) * 2)
            industry_prices[industry] = pd.Series(prices, index=dates)

        # 测试数据库
        db = IndustryMacroDB()
        db.load_industry_data(
            {k: pd.DataFrame({'close': v}) for k, v in industry_prices.items()},
            regime_sequence
        )

        print(f"  ✅ 行业数据库创建成功")

        # 测试选择器
        selector = IndustrySelector(macro_db=db)
        selected = selector.select_by_regime('Regime_1', top_n=3)

        print(f"  ✅ 行业选择成功")
        print(f"     - 选中的行业: {selected}")

        test_results['行业轮动_功能'] = True

    except Exception as e:
        print(f"  ❌ 测试失败: {str(e)}")
        test_results['行业轮动_功能'] = False

    print()


def test_backtest_components():
    """测试回测组件"""
    print("5. 测试Backtrader回测组件...")
    print("-" * 80)

    try:
        # 检查backtrader是否可用
        import backtrader as bt
        print(f"  ✅ Backtrader版本: {bt.__version__}")

        # 尝试导入策略
        from backtest.strategies.macro_strategy import MacroStrategy
        print(f"  ✅ 宏观策略导入成功")

        from backtest.runner.backtest_engine import BacktestEngine
        print(f"  ✅ 回测引擎导入成功")

        test_results['Backtrader组件'] = True

    except Exception as e:
        print(f"  ❌ 测试失败: {str(e)}")
        test_results['Backtrader组件'] = False

    print()


def test_analysis_modules():
    """测试分析模块"""
    print("6. 测试分析与报告模块...")
    print("-" * 80)

    try:
        from backtest.analysis.performance_attribution import PerformanceAttribution
        print(f"  ✅ 绩效归因模块导入成功")

        from backtest.analysis.report_generator import ReportGenerator
        print(f"  ✅ 报告生成器导入成功")

        test_results['分析模块'] = True

    except Exception as e:
        print(f"  ❌ 测试失败: {str(e)}")
        test_results['分析模块'] = False

    print()


def test_dashboard():
    """测试仪表盘"""
    print("7. 测试Streamlit仪表盘...")
    print("-" * 80)

    try:
        import streamlit as st
        print(f"  ✅ Streamlit版本: {st.__version__}")
        print(f"  💡 启动命令: streamlit run dashboard/app.py")

        test_results['仪表盘'] = True

    except Exception as e:
        print(f"  ❌ 测试失败: {str(e)}")
        test_results['仪表盘'] = False

    print()


def print_summary():
    """打印测试摘要"""
    print("=" * 80)
    print("测试摘要")
    print("=" * 80)

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    failed_tests = total_tests - passed_tests

    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests} ✅")
    print(f"失败: {failed_tests} ❌")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    print()

    if failed_tests > 0:
        print("失败的测试:")
        for name, passed in test_results.items():
            if not passed:
                print(f"  ❌ {name}")
    else:
        print("🎉 所有测试通过！所有模块都可以正常使用！")

    print()
    print("=" * 80)
    print("下一步:")
    print("1. 准备历史数据（参考使用指南）")
    print("2. 运行回测: python scripts/run_backtest.py")
    print("3. 启动仪表盘: streamlit run dashboard/app.py")
    print("=" * 80)


def main():
    """主函数"""
    # 运行所有测试
    test_imports()
    test_macro_scorecard()
    test_signal_generator()
    test_industry_rotation()
    test_backtest_components()
    test_analysis_modules()
    test_dashboard()

    # 打印摘要
    print_summary()


if __name__ == "__main__":
    main()
