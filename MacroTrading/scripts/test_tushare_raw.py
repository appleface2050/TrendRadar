"""
测试 Tushare API 原始返回数据
"""
import sys
from pathlib import Path
import tushare as ts
import json

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from configs.db_config import TUSHARE_TOKEN, TUSHARE_HTTP_URL

print("=" * 60)
print("测试 Tushare API 原始返回")
print("=" * 60)

# 初始化 API
pro = ts.pro_api(TUSHARE_TOKEN)
pro._DataApi__token = TUSHARE_TOKEN
pro._DataApi__http_url = TUSHARE_HTTP_URL

print(f"\nAPI URL: {TUSHARE_HTTP_URL}")
print(f"Token: {TUSHARE_TOKEN[:10]}...")

# 测试不同的 API 接口
test_cases = [
    {
        'name': 'PMI (cn_pmi)',
        'method': lambda: pro.cn_pmi(start_date='20240101', limit=5)
    },
    {
        'name': 'CPI (cn_cpi)',
        'method': lambda: pro.cn_cpi(start_date='20240101', limit=5)
    },
    {
        'name': 'GDP (cn_gdp)',
        'method': lambda: pro.cn_gdp(start_date='20240101', limit=5)
    },
]

for test_case in test_cases:
    print(f"\n{'=' * 60}")
    print(f"测试: {test_case['name']}")
    print(f"{'=' * 60}")

    try:
        result = test_case['method']()

        if result is not None:
            print(f"✓ 成功获取数据")
            print(f"返回类型: {type(result)}")

            if hasattr(result, 'columns'):
                print(f"列名: {list(result.columns)}")
            elif hasattr(result, 'keys'):
                print(f"键名: {list(result.keys())}")

            print(f"\n前5条数据:")
            print(result.head() if hasattr(result, 'head') else result)
            print(f"\n数据形状: {result.shape if hasattr(result, 'shape') else 'N/A'}")
        else:
            print("✗ 返回为 None")

    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
