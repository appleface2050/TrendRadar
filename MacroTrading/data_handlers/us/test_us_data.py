"""
测试美国数据获取和管理模块
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data_handlers.us.us_data_fetcher import USDataFetcher
from data_handlers.us.us_data_manager import USDataManager
from data_handlers.us.us_calendar import FREDReleaseCalendar


def test_data_fetcher():
    """测试数据获取器"""
    print("=" * 60)
    print("测试数据获取器")
    print("=" * 60)

    fetcher = USDataFetcher()

    # 测试获取单个指标
    print("\n1. 测试获取 GDP 数据 (最近5条):")
    gdp_data = fetcher.fetch_indicator('GDP', start='2023-01-01')
    if not gdp_data.empty:
        print(gdp_data.tail())
        print(f"✓ 成功获取 {len(gdp_data)} 条 GDP 数据")
    else:
        print("✗ 获取 GDP 数据失败")

    # 测试获取多个指标
    print("\n2. 测试获取核心指标 (CPI, UNRATE, FEDFUNDS):")
    test_indicators = ['CPIAUCSL', 'UNRATE', 'FEDFUNDS']
    multi_data = fetcher.fetch_multiple_indicators(test_indicators, start='2023-01-01')
    if not multi_data.empty:
        print(f"✓ 成功获取 {len(multi_data)} 条数据")
        print("\n各指标数据量:")
        print(multi_data['indicator_code'].value_counts())
    else:
        print("✗ 获取核心指标失败")


def test_data_manager():
    """测试数据管理器"""
    print("\n" + "=" * 60)
    print("测试数据管理器")
    print("=" * 60)

    manager = USDataManager()

    # 测试获取可用指标
    print("\n1. 查询数据库中的指标:")
    indicators = manager.get_available_indicators()
    if not indicators.empty:
        print(f"✓ 找到 {len(indicators)} 个指标:")
        print(indicators[['indicator_code', 'indicator_name', 'start_date', 'end_date']].head(10))
    else:
        print("数据库中暂无数据")

    # 如果有数据，测试查询
    if not indicators.empty:
        print("\n2. 查询 GDP 最近数据:")
        gdp_data = manager.query_data(
            indicator_codes=['GDP'],
            start_date='2020-01-01'
        )
        if not gdp_data.empty:
            print(f"✓ 查询到 {len(gdp_data)} 条数据")
            print(gdp_data.tail())

    manager.close()


def test_calendar():
    """测试发布日历"""
    print("\n" + "=" * 60)
    print("测试发布日历")
    print("=" * 60)

    calendar = FREDReleaseCalendar()

    # 测试估算发布日期
    print("\n1. 估算各种指标的发布日期:")
    test_cases = [
        ('CPIAUCSL', '2024-01-01', '2024年1月CPI'),
        ('GDP', '2024-03-31', '2024年Q1 GDP'),
        ('PAYEMS', '2024-01-01', '2024年1月非农'),
        ('DGS10', '2024-01-15', '10年期国债收益率'),
    ]

    for code, ref_date, desc in test_cases:
        release_date = calendar.estimate_release_date(code, ref_date)
        if release_date:
            print(f"✓ {desc}: 参考日期 {ref_date} → 预计发布 {release_date}")
        else:
            print(f"✗ {desc}: 估算失败")


if __name__ == "__main__":
    print("\n开始测试美国数据模块...\n")

    # 测试数据获取器
    test_data_fetcher()

    # 测试数据管理器
    test_data_manager()

    # 测试发布日历
    test_calendar()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
