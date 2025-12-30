"""
美国宏观数据管理器
负责数据的存储、查询和更新
"""
import pandas as pd
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List, Optional, Dict
import logging
from datetime import datetime
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.db_config import DATABASE_URL, DB_CONFIG, DATABASE_NAME

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class USDataManager:
    """美国宏观数据管理器"""

    def __init__(self):
        """初始化数据管理器"""
        self.engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def save_data(self, df: pd.DataFrame, table_name: str = 'us_macro_data') -> bool:
        """
        将数据保存到数据库

        Args:
            df: 包含宏观数据的 DataFrame
            table_name: 目标表名

        Returns:
            是否成功保存
        """
        try:
            if df.empty:
                logger.warning("DataFrame 为空，无法保存")
                return False

            # 选择需要的列
            columns_mapping = {
                'indicator_code': 'indicator_code',
                'indicator_name': 'indicator_name',
                'date': 'date',
                'value': 'value',
                'frequency': 'frequency',
            }

            # 只保留存在的列
            existing_columns = [col for col in columns_mapping.keys() if col in df.columns]
            df_to_save = df[existing_columns].copy()

            # 转换日期格式
            if 'date' in df_to_save.columns:
                df_to_save['date'] = pd.to_datetime(df_to_save['date'])

            # 保存到数据库
            rows_affected = df_to_save.to_sql(
                table_name,
                self.engine,
                if_exists='append',
                index=False,
                method='multi'
            )

            logger.info(f"成功保存 {rows_affected} 条数据到表 {table_name}")
            return True

        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")
            return False

    def query_data(self,
                   indicator_codes: Optional[List[str]] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   table_name: str = 'us_macro_data') -> pd.DataFrame:
        """
        从数据库查询数据

        Args:
            indicator_codes: 指标代码列表，None 表示查询所有
            start_date: 开始日期
            end_date: 结束日期
            table_name: 表名

        Returns:
            包含查询结果的 DataFrame
        """
        try:
            # 构建 SQL 查询
            query = f"SELECT * FROM {table_name} WHERE 1=1"

            if indicator_codes:
                codes_str = "','".join(indicator_codes)
                query += f" AND indicator_code IN ('{codes_str}')"

            if start_date:
                query += f" AND date >= '{start_date}'"

            if end_date:
                query += f" AND date <= '{end_date}'"

            query += " ORDER BY indicator_code, date"

            # 执行查询
            df = pd.read_sql(query, self.engine)

            logger.info(f"从 {table_name} 查询到 {len(df)} 条数据")

            return df

        except Exception as e:
            logger.error(f"查询数据失败: {str(e)}")
            return pd.DataFrame()

    def get_latest_date(self, indicator_code: str, table_name: str = 'us_macro_data') -> Optional[str]:
        """
        获取某个指标的最新数据日期

        Args:
            indicator_code: 指标代码
            table_name: 表名

        Returns:
            最新日期字符串，如果没有数据则返回 None
        """
        try:
            query = f"""
                SELECT MAX(date) as latest_date
                FROM {table_name}
                WHERE indicator_code = '{indicator_code}'
            """

            result = pd.read_sql(query, self.engine)

            if not result.empty and result['latest_date'].iloc[0]:
                return result['latest_date'].iloc[0].strftime('%Y-%m-%d')
            else:
                return None

        except Exception as e:
            logger.error(f"获取最新日期失败: {str(e)}")
            return None

    def update_data(self, df: pd.DataFrame, table_name: str = 'us_macro_data') -> bool:
        """
        更新数据库中的数据（先删除后插入）

        Args:
            df: 包含新数据的 DataFrame
            table_name: 表名

        Returns:
            是否成功更新
        """
        try:
            if df.empty or 'indicator_code' not in df.columns or 'date' not in df.columns:
                logger.warning("DataFrame 格式不正确，无法更新")
                return False

            # 删除旧数据
            indicator_codes = df['indicator_code'].unique()

            for code in indicator_codes:
                delete_query = f"""
                    DELETE FROM {table_name}
                    WHERE indicator_code = '{code}'
                """
                with self.engine.connect() as conn:
                    conn.execute(text(delete_query))

            # 插入新数据
            return self.save_data(df, table_name)

        except Exception as e:
            logger.error(f"更新数据失败: {str(e)}")
            return False

    def get_available_indicators(self, table_name: str = 'us_macro_data') -> pd.DataFrame:
        """
        获取数据库中所有可用的指标

        Args:
            table_name: 表名

        Returns:
            包含指标信息的 DataFrame
        """
        try:
            query = f"""
                SELECT
                    indicator_code,
                    indicator_name,
                    MIN(date) as start_date,
                    MAX(date) as end_date,
                    COUNT(*) as count
                FROM {table_name}
                GROUP BY indicator_code, indicator_name
                ORDER BY indicator_code
            """

            df = pd.read_sql(query, self.engine)

            logger.info(f"找到 {len(df)} 个指标")
            return df

        except Exception as e:
            logger.error(f"获取可用指标失败: {str(e)}")
            return pd.DataFrame()

    def get_data_by_date(self,
                         date: str,
                         table_name: str = 'us_macro_data') -> pd.DataFrame:
        """
        获取指定日期可用的所有数据（用于回测时的点数据）

        Args:
            date: 日期字符串
            table_name: 表名

        Returns:
            包含该日期可用数据的 DataFrame
        """
        try:
            query = f"""
                SELECT * FROM {table_name}
                WHERE date <= '{date}'
                AND (release_date IS NULL OR release_date <= '{date}')
                ORDER BY indicator_code, date DESC
            """

            df = pd.read_sql(query, self.engine)

            # 对每个指标，只取最新的那条
            if not df.empty:
                df = df.groupby('indicator_code').first().reset_index()

            return df

        except Exception as e:
            logger.error(f"获取日期 {date} 的数据失败: {str(e)}")
            return pd.DataFrame()

    def close(self):
        """关闭数据库连接"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()


# 测试代码
if __name__ == "__main__":
    manager = USDataManager()

    # 测试获取可用指标
    print("\n获取可用指标:")
    indicators = manager.get_available_indicators()
    if not indicators.empty:
        print(indicators)

    # 测试查询数据
    print("\n查询 GDP 数据:")
    gdp_data = manager.query_data(indicator_codes=['GDP'], start_date='2020-01-01')
    if not gdp_data.empty:
        print(gdp_data.head())

    manager.close()
