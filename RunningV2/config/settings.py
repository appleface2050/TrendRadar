"""
配置管理模块
集中管理数据库配置、CSV路径、字段映射等
"""
import sys
import os

# 添加项目路径以便导入数据库配置
sys.path.insert(0, '/home/shang/git')
from confs.mysql import mysql_running_conf

# ==================== 数据库配置 ====================
DB_CONFIG = mysql_running_conf

# ==================== CSV 文件路径配置 ====================
# 项目根目录
BASE_DIR = '/home/shang/git/Indeptrader/RunningV2'

# CSV 文件目录
CSV_DIR = os.path.join(BASE_DIR, 'csv')

# CSV 文件路径
CSV_FILES = {
    'records': os.path.join(CSV_DIR, 'records.csv'),
    'rq': os.path.join(CSV_DIR, 'rq.csv'),
    'shoe_info': os.path.join(CSV_DIR, 'shoe_info.csv')
}

# ==================== 字段映射配置 ====================
# CSV 字段名到数据库字段名的映射
FIELD_MAPPINGS = {
    'rq': {
        '日期': 'date',
        'RQ': 'rq',
        'status': 'status',
        'physical power': 'physical_power',
        'fatigue': 'fatigue'
    },
    'shoe_info': {
        'name': 'shoe'
    }
}

# ==================== 同步策略配置 ====================
# 同步模式：'periodic'（定时）或 'watch'（实时监控）
SYNC_MODE = 'periodic'

# 定时同步间隔（秒）
SYNC_INTERVAL = 300  # 5分钟

# ==================== 日志配置 ====================
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'INFO'

# 日志文件路径
LOG_FILE = os.path.join(BASE_DIR, 'sync.log')
