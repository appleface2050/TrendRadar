"""
数据库配置文件
MacroTrading 项目数据库连接配置
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'charset': 'utf8mb4'
}

# 数据库名称
DATABASE_NAME = 'MacroTrading'

# 完整的数据库连接 URL
DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DATABASE_NAME}?charset=utf8mb4"

# FRED API 配置（从环境变量或直接设置）
FRED_API_KEY = os.getenv('FRED_API_KEY', '')

# Tushare API 配置
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN', '')
