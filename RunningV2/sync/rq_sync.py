"""
rq.csv 同步模块
将 csv/rq.csv 同步到 running_rq_record 表
"""
import sys
sys.path.insert(0, '/home/shang/git')
sys.path.insert(0, '/home/shang/git/Indeptrader')

from sync.base import BaseSync
from Running.running_models import DailyRQRecord
from config.settings import CSV_FILES, FIELD_MAPPINGS


class RQSync(BaseSync):
    """RQ 能力值数据同步类"""

    def get_model(self):
        """返回 ORM 模型"""
        return DailyRQRecord

    def get_csv_path(self):
        """返回 CSV 文件路径"""
        return CSV_FILES['rq']

    def get_unique_fields(self):
        """返回唯一键字段"""
        return ['date']

    def preprocess_row(self, row):
        """
        预处理单行数据
        处理字段名映射和空值
        """
        # 字段映射
        mapping = FIELD_MAPPINGS['rq']

        # 构建数据字典
        data = {}
        for csv_field, db_field in mapping.items():
            # 获取 CSV 中的值，如果不存在则设为 "0"
            value = row.get(csv_field, "0")

            # 处理空值
            if value == "" or value is None:
                value = "0"

            data[db_field] = str(value)

        return data


# 测试代码
if __name__ == '__main__':
    syncer = RQSync()
    syncer.sync()
