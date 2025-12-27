"""
基础同步类
提供通用的 CSV 读取、去重检查、插入逻辑
"""
import sys
import pandas as pd
import datetime
from abc import ABC, abstractmethod
from sqlalchemy.sql import exists

# 添加项目路径
sys.path.insert(0, '/home/shang/git')
sys.path.insert(0, '/home/shang/git/Indeptrader')
from Running.running_models import session


class BaseSync(ABC):
    """
    基础同步类（抽象类）
    所有具体的同步类应该继承此类并实现抽象方法
    """

    def __init__(self):
        self.session = session

    @abstractmethod
    def get_model(self):
        """
        返回 ORM 模型类
        子类必须实现此方法
        """
        pass

    @abstractmethod
    def get_csv_path(self):
        """
        返回 CSV 文件路径
        子类必须实现此方法
        """
        pass

    @abstractmethod
    def get_unique_fields(self):
        """
        返回用于去重的字段列表
        子类必须实现此方法
        例如：['date'] 或 ['date', 'shoe']
        """
        pass

    @abstractmethod
    def preprocess_row(self, row):
        """
        预处理单行数据
        子类必须实现此方法
        返回字典：{字段名: 值}
        """
        pass

    def read_csv(self):
        """
        读取 CSV 文件并返回 DataFrame
        """
        csv_path = self.get_csv_path()
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            # 填充空值
            df = df.fillna("")
            return df
        except Exception as e:
            print(f"[ERROR] 读取 CSV 文件失败: {csv_path}, 错误: {e}")
            raise

    def row_exists(self, row_data):
        """
        检查记录是否已存在于数据库中

        Args:
            row_data: 预处理后的数据字典

        Returns:
            bool: True 表示已存在，False 表示不存在
        """
        model = self.get_model()
        unique_fields = self.get_unique_fields()

        # 构建查询条件
        conditions = []
        for field in unique_fields:
            if field in row_data:
                # 获取模型字段
                model_field = getattr(model, field)
                conditions.append(model_field == row_data[field])

        if not conditions:
            return False

        # 检查是否存在
        query = self.session.query(exists().where(*conditions)).scalar()
        return query

    def insert_row(self, row_data):
        """
        插入单条记录到数据库

        Args:
            row_data: 预处理后的数据字典

        Returns:
            bool: True 表示成功，False 表示失败
        """
        model = self.get_model()

        try:
            # 创建 ORM 对象
            obj = model()
            for key, value in row_data.items():
                setattr(obj, key, value)

            # 设置更新时间
            if hasattr(obj, 'uptime'):
                obj.uptime = datetime.datetime.now()

            # 插入数据库
            self.session.add(obj)
            self.session.commit()

            return True
        except Exception as e:
            self.session.rollback()
            print(f"[ERROR] 插入数据失败: {row_data}, 错误: {e}")
            return False

    def sync(self):
        """
        主同步逻辑
        遍历 CSV → 检查去重 → 插入新数据
        """
        csv_path = self.get_csv_path()
        model_name = self.get_model().__tablename__

        print(f"\n{'='*60}")
        print(f"开始同步: {csv_path} → {model_name}")
        print(f"{'='*60}")

        try:
            # 读取 CSV
            df = self.read_csv()
            total_rows = len(df)
            print(f"CSV 文件总记录数: {total_rows}")

            # 统计
            new_count = 0
            skip_count = 0
            error_count = 0

            # 遍历每一行
            for index, row in df.iterrows():
                try:
                    # 预处理数据
                    row_data = self.preprocess_row(row)

                    # 检查是否已存在
                    if self.row_exists(row_data):
                        skip_count += 1
                        continue

                    # 插入新数据
                    if self.insert_row(row_data):
                        new_count += 1
                        print(f"[{index+1}/{total_rows}] 插入新记录: {row_data}")
                    else:
                        error_count += 1

                except Exception as e:
                    error_count += 1
                    print(f"[ERROR] 处理第 {index+1} 行失败: {e}")

            # 输出统计信息
            print(f"\n{'='*60}")
            print(f"同步完成:")
            print(f"  总记录数: {total_rows}")
            print(f"  新插入: {new_count}")
            print(f"  跳过(已存在): {skip_count}")
            print(f"  失败: {error_count}")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"[ERROR] 同步失败: {e}")
            raise
