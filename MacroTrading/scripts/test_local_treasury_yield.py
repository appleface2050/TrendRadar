"""
测试从本地CSV文件读取美国国债收益率数据
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

print("=" * 100)
print("测试本地CSV美国国债收益率数据读取")
print("=" * 100)
print()

from data.flow.flow_fetcher import FlowDataFetcher
from configs.db_config import load_confidential_config

config = load_confidential_config()

fetcher = FlowDataFetcher(
    tushare_token=config.get('TUSHARE_DataApi__token'),
    fred_key=config.get('FRED_API_Key')
)

# 测试获取10年期国债收益率（最近3年）
print("测试获取10年期美国国债收益率...")
print("-" * 100)

end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')

print(f"日期范围：{start_date} 至 {end_date}")
print()

us_yield_10y = fetcher.get_us_treasury_yield(start_date, end_date, maturity='10y', use_local=True)

if us_yield_10y is not None and len(us_yield_10y) > 0:
    print(f"\n✓ 成功获取10年期国债收益率数据")
    print(f"  记录数：{len(us_yield_10y)}条")
    print(f"  时间范围：{us_yield_10y.index.min()} 至 {us_yield_10y.index.max()}")
    print(f"  平均收益率：{us_yield_10y['us_treasury_10y'].mean():.2f}%")
    print(f"  最新收益率：{us_yield_10y['us_treasury_10y'].iloc[-1]:.2f}%")
    print(f"  最高收益率：{us_yield_10y['us_treasury_10y'].max():.2f}%")
    print(f"  最低收益率：{us_yield_10y['us_treasury_10y'].min():.2f}%")

    print(f"\n数据预览：")
    print(us_yield_10y.head(10))

    print(f"\n数据尾部：")
    print(us_yield_10y.tail(10))
else:
    print("\n✗ 获取失败")

# 测试其他期限
print("\n\n" + "=" * 100)
print("测试获取其他期限国债收益率...")
print("-" * 100)

maturities = ['2y', '5y', '10y', '30y']

for maturity in maturities:
    print(f"\n{maturity}国债收益率：")
    yield_data = fetcher.get_us_treasury_yield(start_date, end_date, maturity=maturity, use_local=True)

    if yield_data is not None and len(yield_data) > 0:
        print(f"  ✓ 记录数：{len(yield_data)}条")
        print(f"  最新收益率：{yield_data.iloc[-1, 0]:.2f}%")
    else:
        print(f"  ✗ 获取失败")

print("\n\n" + "=" * 100)
print("测试完成！")
print("=" * 100)
