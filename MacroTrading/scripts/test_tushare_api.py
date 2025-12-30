"""
测试 Tushare API 连接
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data_handlers.cn.tushare_fetcher import CNDataFetcher

print("=" * 60)
print("测试 Tushare API 连接")
print("=" * 60)

print("\n初始化数据获取器...")
fetcher = CNDataFetcher()

if fetcher.pro:
    print("✓ Tushare API 初始化成功")
    print(f"✓ Token: {fetcher.token[:10]}...")
    print(f"✓ Endpoint: {fetcher.pro._DataApi__http_url}")

    # 测试获取一个简单指标
    print("\n测试获取 PMI 数据...")
    try:
        pmi_data = fetcher.fetch_pmi(start_date='20240101')
        if not pmi_data.empty:
            print(f"✓ 成功获取 PMI 数据: {len(pmi_data)} 条")
            print(pmi_data.head())
        else:
            print("✗ PMI 数据为空")
    except Exception as e:
        print(f"✗ 获取 PMI 数据失败: {str(e)}")
else:
    print("✗ Tushare API 初始化失败")
    print("请检查 confidential.json 中的配置")

print("\n" + "=" * 60)
