"""
shoe_info.csv 同步模块
将 csv/shoe_info.csv 同步到 running_shoe_info 表
"""
import sys
sys.path.insert(0, '/home/shang/git')
sys.path.insert(0, '/home/shang/git/Indeptrader')

from sync.base import BaseSync
from Running.running_models import ShoeInfo
from config.settings import CSV_FILES, FIELD_MAPPINGS


class ShoeInfoSync(BaseSync):
    """跑鞋信息数据同步类"""

    def get_model(self):
        """返回 ORM 模型"""
        return ShoeInfo

    def get_csv_path(self):
        """返回 CSV 文件路径"""
        return CSV_FILES['shoe_info']

    def get_unique_fields(self):
        """
        返回唯一键字段
        使用 shoe（对应 CSV 的 name）作为唯一键
        """
        return ['shoe']

    def preprocess_row(self, row):
        """
        预处理单行数据
        处理字段名映射（name → shoe）
        """
        # CSV 字段名
        csv_fields = [
            'name', 'brand', 'price', 'color',
            'start_date', 'end_date', 'shortage', 'sold_price'
        ]

        # 构建数据字典
        data = {}
        for csv_field in csv_fields:
            # 获取 CSV 中的值
            value = row.get(csv_field, "")

            # 处理空值
            if value == "" or value is None:
                # price 和 sold_price 是 Float 类型，设为 0.0
                if csv_field in ['price', 'sold_price']:
                    value = 0.0
                else:
                    value = ""

            # 字段名映射：name → shoe
            if csv_field == 'name':
                data['shoe'] = value
            else:
                data[csv_field] = value

        # 确保 price 和 sold_price 是 Float 类型
        try:
            data['price'] = float(data['price']) if data['price'] else 0.0
        except (ValueError, TypeError):
            data['price'] = 0.0

        try:
            data['sold_price'] = float(data['sold_price']) if data['sold_price'] else 0.0
        except (ValueError, TypeError):
            data['sold_price'] = 0.0

        return data


# 测试代码
if __name__ == '__main__':
    syncer = ShoeInfoSync()
    syncer.sync()
