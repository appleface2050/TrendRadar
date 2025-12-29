"""
数据库配置文件
MacroTrading 项目数据库连接配置
"""
import os
import json
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

# 从 confidential.json 读取 API 密钥
def load_confidential_config():
    """从 confidential.json 加载配置"""
    try:
        conf_file = BASE_DIR.parent / 'confidential.json'
        if conf_file.exists():
            with open(conf_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"警告: 未找到 {conf_file}，使用默认配置")
            return {}
    except Exception as e:
        print(f"加载配置文件失败: {str(e)}")
        return {}

# 加载配置
_conf = load_confidential_config()

# FRED API 配置
FRED_API_KEY = _conf.get('FRED_API_Key', os.getenv('FRED_API_KEY', ''))

# Tushare API 配置（特殊 endpoint）
TUSHARE_TOKEN = _conf.get('TUSHARE_DataApi__token', os.getenv('TUSHARE_TOKEN', ''))
TUSHARE_HTTP_URL = _conf.get('TUSHARE_DataApi__http_url', 'http://1w1a.xiximiao.com/dataapi')
