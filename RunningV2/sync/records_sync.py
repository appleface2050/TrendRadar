"""
records.csv 同步模块
将 csv/records.csv 同步到 running_shoe_record 表
"""
import sys
sys.path.insert(0, '/home/shang/git')
sys.path.insert(0, '/home/shang/git/Indeptrader')

from sync.base import BaseSync
from Running.running_models import DailyShoeRecord
from config.settings import CSV_FILES


class RecordsSync(BaseSync):
    """跑步记录数据同步类"""

    def get_model(self):
        """返回 ORM 模型"""
        return DailyShoeRecord

    def get_csv_path(self):
        """返回 CSV 文件路径"""
        return CSV_FILES['records']

    def get_unique_fields(self):
        """
        返回唯一键字段
        使用 date + shoe 组合作为唯一键
        """
        return ['date', 'shoe']

    def preprocess_row(self, row):
        """
        预处理单行数据
        处理字段映射和 rq_inc 字段
        """
        # CSV 字段名
        csv_fields = [
            'date', 'distance', 'used_time', 'average_heart_rate',
            'cadence', 'shoe', 'type', 'rq', 'EMTIR'
        ]

        # 构建数据字典
        data = {}
        for field in csv_fields:
            # 获取 CSV 中的值，如果不存在则设为默认值
            value = row.get(field, "")

            # 处理空值
            if value == "" or value is None:
                # 根据字段类型设置默认值
                if field in ['used_time', 'EMTIR']:
                    value = ""
                else:
                    value = "0"

            data[field] = str(value)

        # 添加 rq_inc 字段（CSV 中无此字段，统一设为 "0"）
        data['rq_inc'] = "0"

        return data


# 测试代码
if __name__ == '__main__':
    syncer = RecordsSync()
    syncer.sync()
