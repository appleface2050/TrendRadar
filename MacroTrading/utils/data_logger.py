"""
数据处理日志记录器

提供统一的日志记录机制，追踪数据处理过程
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class DataLogger:
    """数据处理日志记录器"""

    def __init__(self, log_file: Optional[str] = None, name: str = 'DataProcessing'):
        """
        初始化日志记录器

        Args:
            log_file: 日志文件路径（可选，默认输出到终端）
            name: 日志记录器名称
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 清除已有的处理器
        self.logger.handlers.clear()

        # 创建格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 终端处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器（可选）
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log_step(self, step_name: str, details: str = ''):
        """
        记录处理步骤

        Args:
            step_name: 步骤名称
            details: 详细信息
        """
        message = f"[{step_name}]"
        if details:
            message += f" {details}"
        self.logger.info(message)

    def log_success(self, step_name: str, details: str = ''):
        """
        记录成功

        Args:
            step_name: 步骤名称
            details: 详细信息
        """
        message = f"✅ [{step_name}]"
        if details:
            message += f" {details}"
        self.logger.info(message)

    def log_error(self, step_name: str, error: Exception):
        """
        记录错误

        Args:
            step_name: 步骤名称
            error: 异常对象
        """
        message = f"❌ [{step_name}] {type(error).__name__}: {str(error)}"
        self.logger.error(message)

    def log_warning(self, step_name: str, message: str):
        """
        记录警告

        Args:
            step_name: 步骤名称
            message: 警告消息
        """
        warning_msg = f"⚠️  [{step_name}] {message}"
        self.logger.warning(warning_msg)

    def log_quality_stats(self, stats: dict):
        """
        记录数据质量统计

        Args:
            stats: 质量统计字典
        """
        self.logger.info("📊 数据质量统计:")
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                self.logger.info(f"   - {key}: {value:,}")
            elif isinstance(value, dict):
                self.logger.info(f"   - {key}:")
                for k, v in value.items():
                    self.logger.info(f"     - {k}: {v:,}")
            else:
                self.logger.info(f"   - {key}: {value}")

    def log_info(self, message: str):
        """
        记录普通信息

        Args:
            message: 消息内容
        """
        self.logger.info(message)

    def log_debug(self, message: str):
        """
        记录调试信息

        Args:
            message: 消息内容
        """
        self.logger.debug(message)
