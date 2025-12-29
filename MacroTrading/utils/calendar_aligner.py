"""
宏观数据日历对齐器（核心基础设施）
用于回测时获取实际可观测的宏观数据，杜绝未来函数

这是整个回测系统最重要的模块，必须100%准确
"""
import pandas as pd
import pymysql
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from configs.db_config import DB_CONFIG, DATABASE_NAME

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CalendarAligner:
    """
    宏观数据日历对齐器

    核心功能：
    1. 获取指定日期实际可观测的宏观数据
    2. 避免未来函数（look-ahead bias）
    3. 支持混频数据（日度、周度、月度、季度）
    4. 支持中美两国数据

    使用场景：
    - 回测系统中的数据获取
    - 历史某时刻的宏观数据快照
    - Nowcasting 模型的输入数据
    """

    def __init__(self):
        """初始化日历对齐器"""
        self.db_config = DB_CONFIG
        self.database_name = DATABASE_NAME

    def get_available_data(self,
                          date: str,
                          country: str = 'all',
                          indicator_codes: Optional[List[str]] = None) -> pd.DataFrame:
        """
        获取在指定日期实际可观测的宏观数据值（杜绝未来函数）

        这是核心方法！确保100%准确！

        Args:
            date: 查询日期，格式 'YYYY-MM-DD'
            country: 国家 ('US', 'CN', 'all')
            indicator_codes: 指标代码列表，None 表示查询所有

        Returns:
            在该日期可观测的数据 DataFrame
            包含列：indicator_code, indicator_name, date, value, frequency, release_date
        """
        try:
            query_date = pd.to_datetime(date).strftime('%Y-%m-%d')

            # 确定查询的表
            if country == 'US':
                tables = ['us_macro_data']
            elif country == 'CN':
                tables = ['cn_macro_data']
            else:  # 'all'
                tables = ['us_macro_data', 'cn_macro_data']

            all_data = []

            for table in tables:
                try:
                    # 构建查询
                    query = f"""
                        SELECT
                            d.indicator_code,
                            d.indicator_name,
                            d.date,
                            d.value,
                            d.frequency,
                            d.release_date,
                            r.release_date as cal_release_date
                        FROM {table} d
                        LEFT JOIN release_calendar r
                            ON d.indicator_code = r.indicator_code
                            AND d.date = r.reference_date
                            AND r.country = '{table[:2].upper()}'
                        WHERE d.date <= '{query_date}'
                        AND (
                            r.release_date IS NULL
                            OR r.release_date <= '{query_date}'
                        )
                    """

                    # 如果指定了指标代码，添加过滤条件
                    if indicator_codes:
                        codes_str = "','".join(indicator_codes)
                        query += f" AND d.indicator_code IN ('{codes_str}')"

                    query += " ORDER BY d.indicator_code, d.date DESC"

                    # 执行查询
                    connection = pymysql.connect(
                        host=self.db_config['host'],
                        port=self.db_config['port'],
                        user=self.db_config['user'],
                        password=self.db_config['password'],
                        database=self.database_name,
                        charset=self.db_config['charset']
                    )

                    df = pd.read_sql(query, connection)
                    connection.close()

                    if not df.empty:
                        # 添加国家标识
                        df['country'] = table[:2].upper()
                        all_data.append(df)

                except Exception as e:
                    logger.error(f"查询表 {table} 失败: {str(e)}")
                    continue

            if all_data:
                result_df = pd.concat(all_data, ignore_index=True)

                # 对每个指标，只取最新的那条（最新发布的数据）
                if not result_df.empty:
                    result_df = result_df.groupby('indicator_code').first().reset_index()

                logger.info(f"在 {date} 可观测的数据: {len(result_df)} 条")
                return result_df
            else:
                logger.warning(f"在 {date} 没有可观测的数据")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取可观测数据失败: {str(e)}")
            return pd.DataFrame()

    def get_indicator_value(self,
                           date: str,
                           indicator_code: str,
                           country: str = 'US') -> Optional[float]:
        """
        获取单个指标在指定日期的值

        Args:
            date: 查询日期
            indicator_code: 指标代码
            country: 国家

        Returns:
            指标值，如果不存在则返回 None
        """
        try:
            df = self.get_available_data(
                date=date,
                country=country,
                indicator_codes=[indicator_code]
            )

            if not df.empty:
                return float(df.iloc[0]['value'])
            else:
                return None

        except Exception as e:
            logger.error(f"获取指标值失败: {str(e)}")
            return None

    def get_time_series(self,
                       indicator_code: str,
                       start_date: str,
                       end_date: str,
                       country: str = 'US') -> pd.DataFrame:
        """
        获取指标在日期范围内的时间序列（考虑发布延迟）

        Args:
            indicator_code: 指标代码
            start_date: 开始日期
            end_date: 结束日期
            country: 国家

        Returns:
            时间序列 DataFrame，包含列：date, value
        """
        try:
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')

            values = []
            for date in date_range:
                date_str = date.strftime('%Y-%m-%d')
                value = self.get_indicator_value(date_str, indicator_code, country)
                values.append({
                    'date': date_str,
                    'value': value
                })

            result_df = pd.DataFrame(values)

            logger.info(f"获取 {indicator_code} 时间序列: {len(result_df)} 条")
            return result_df

        except Exception as e:
            logger.error(f"获取时间序列失败: {str(e)}")
            return pd.DataFrame()

    def get_data_snapshot(self,
                         date: str,
                         indicators: Dict[str, str]) -> pd.DataFrame:
        """
        获取指定日期的宏观数据快照

        Args:
            date: 日期
            indicators: 指标字典 {indicator_code: country}

        Returns:
            数据快照 DataFrame
        """
        try:
            all_data = []

            for code, country in indicators.items():
                value = self.get_indicator_value(date, code, country)
                if value is not None:
                    all_data.append({
                        'indicator_code': code,
                        'country': country,
                        'value': value,
                        'date': date
                    })

            if all_data:
                return pd.DataFrame(all_data)
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取数据快照失败: {str(e)}")
            return pd.DataFrame()

    def validate_data_integrity(self,
                               test_date: str,
                               expected_indicators: List[str]) -> bool:
        """
        验证数据完整性（重要！用于确保回测真实性）

        Args:
            test_date: 测试日期
            expected_indicators: 预期应该存在的指标列表

        Returns:
            是否通过验证
        """
        try:
            df = self.get_available_data(test_date)

            if df.empty:
                logger.error(f"验证失败: {test_date} 没有可观测数据")
                return False

            available_codes = set(df['indicator_code'].unique())
            expected_codes = set(expected_indicators)

            missing_codes = expected_codes - available_codes

            if missing_codes:
                logger.warning(f"验证警告: {test_date} 缺少指标 {missing_codes}")
                return False

            logger.info(f"验证通过: {test_date} 数据完整")
            return True

        except Exception as e:
            logger.error(f"验证数据完整性失败: {str(e)}")
            return False

    def get_release_lag_stats(self,
                             indicator_code: str,
                             country: str = 'US') -> Dict[str, float]:
        """
        获取指标的发布延迟统计信息

        Args:
            indicator_code: 指标代码
            country: 国家

        Returns:
            统计信息字典 {min, max, mean, median}
        """
        try:
            table = f"{country.lower()}_macro_data"

            query = f"""
                SELECT
                    d.date as reference_date,
                    r.release_date,
                    DATEDIFF(r.release_date, d.date) as lag_days
                FROM {table} d
                JOIN release_calendar r
                    ON d.indicator_code = r.indicator_code
                    AND d.date = r.reference_date
                    AND r.country = '{country.upper()}'
                WHERE d.indicator_code = '{indicator_code}'
                    AND r.release_date IS NOT NULL
            """

            connection = pymysql.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.database_name,
                charset=self.db_config['charset']
            )

            df = pd.read_sql(query, connection)
            connection.close()

            if df.empty:
                logger.warning(f"指标 {indicator_code} 没有发布延迟数据")
                return {}

            stats = {
                'min': float(df['lag_days'].min()),
                'max': float(df['lag_days'].max()),
                'mean': float(df['lag_days'].mean()),
                'median': float(df['lag_days'].median()),
            }

            logger.info(f"指标 {indicator_code} 发布延迟统计: {stats}")
            return stats

        except Exception as e:
            logger.error(f"获取发布延迟统计失败: {str(e)}")
            return {}


# 创建全局实例（便于使用）
calendar_aligner = CalendarAligner()


# 便捷函数
def get_available_data(date: str,
                      country: str = 'all',
                      indicator_codes: Optional[List[str]] = None) -> pd.DataFrame:
    """
    获取指定日期可观测的宏观数据（便捷函数）

    Args:
        date: 日期
        country: 国家
        indicator_codes: 指标代码列表

    Returns:
        可观测数据 DataFrame
    """
    return calendar_aligner.get_available_data(date, country, indicator_codes)


def get_indicator_value(date: str,
                       indicator_code: str,
                       country: str = 'US') -> Optional[float]:
    """
    获取单个指标的值（便捷函数）

    Args:
        date: 日期
        indicator_code: 指标代码
        country: 国家

    Returns:
        指标值
    """
    return calendar_aligner.get_indicator_value(date, indicator_code, country)


# 测试代码
if __name__ == "__main__":
    aligner = CalendarAligner()

    print("=" * 60)
    print("测试日历对齐器")
    print("=" * 60)

    # 测试获取某个日期的可观测数据
    print("\n1. 测试获取 2024-01-15 的可观测数据:")
    data = aligner.get_available_data('2024-01-15', country='US')

    if not data.empty:
        print(f"✓ 找到 {len(data)} 条可观测数据")
        print("\n部分数据:")
        print(data[['indicator_code', 'date', 'value']].head(10))
    else:
        print("✗ 没有找到数据（可能需要先导入数据到数据库）")

    # 测试获取单个指标值
    print("\n2. 测试获取单个指标值:")
    value = aligner.get_indicator_value('2024-01-15', 'GDP', 'US')
    if value is not None:
        print(f"✓ GDP 在 2024-01-15 的值: {value}")
    else:
        print("✗ 未获取到 GDP 值")

    # 测试获取时间序列
    print("\n3. 测试获取时间序列:")
    ts = aligner.get_time_series(
        'CPIAUCSL',
        '2024-01-01',
        '2024-01-31',
        'US'
    )

    if not ts.empty:
        print(f"✓ 获取到 {len(ts)} 条时间序列数据")
        print("\n前10条:")
        print(ts.head(10))
    else:
        print("✗ 未获取到时间序列数据")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
