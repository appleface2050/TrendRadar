"""
测试中国数据 API 返回格式
"""
import sys
from pathlib import Path
import tushare as ts

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from configs.db_config import TUSHARE_TOKEN, TUSHARE_HTTP_URL

# 初始化 API
pro = ts.pro_api(TUSHARE_TOKEN)
pro._DataApi__token = TUSHARE_TOKEN
pro._DataApi__http_url = TUSHARE_HTTP_URL

print("=" * 60)
print("测试中国数据 API")
print("=" * 60)

# 测试 GDP
print("\n1. GDP 数据:")
try:
    gdp = pro.cn_gdp(start_date='20240101', limit=3)
    print(f"列名: {list(gdp.columns)}")
    print(gdp.head())
except Exception as e:
    print(f"错误: {e}")

# 测试货币供应量
print("\n2. 货币供应量数据:")
try:
    m = pro.cn_m(start_date='20240101', limit=3)
    print(f"列名: {list(m.columns)}")
    print(m.head())
except Exception as e:
    print(f"错误: {e}")

# 测试 Shibor
print("\n3. Shibor 数据:")
try:
    shibor = pro.shibor(start_date='20240101', end_date='20240110')
    print(f"列名: {list(shibor.columns)}")
    print(shibor.head())
except Exception as e:
    print(f"错误: {e}")

print("\n" + "=" * 60)
