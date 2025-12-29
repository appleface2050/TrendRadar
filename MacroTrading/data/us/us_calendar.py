"""
美国宏观数据发布日历
记录 FRED 数据的发布时间，用于回测时避免未来函数
"""
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.db_config import DB_CONFIG, DATABASE_NAME
import pymysql

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FREDReleaseCalendar:
    """FRED 数据发布日历管理器"""

    # FRED 发布日历 URL（如果有的话）
    FRED_RELEASE_CALENDAR_URL = "https://fred.stlouisfed.org/release"

    # 主要指标的发布时间规则（经验数据）
    # 格式：'指标代码': {'day_of_month': X, 'time': 'HH:MM', 'timezone': 'EST'}
    RELEASE_SCHEDULE = {
        # GDP - 季度，季度结束后约1个月发布
        'GDP': {
            'frequency': 'quarterly',
            'release_lag_days': 30,  # 季度结束后约30天发布
            'release_time': '08:30',
            'timezone': 'EST'
        },

        # CPI - 月度，次月中旬发布
        'CPIAUCSL': {
            'frequency': 'monthly',
            'release_day': '15',  # 约每月15号
            'release_time': '08:30',
            'timezone': 'EST'
        },
        'CPILFESL': {
            'frequency': 'monthly',
            'release_day': '15',
            'release_time': '08:30',
            'timezone': 'EST'
        },

        # 非农就业 - 月度，每月第一个周五
        'PAYEMS': {
            'frequency': 'monthly',
            'release_pattern': 'first_friday',
            'release_time': '08:30',
            'timezone': 'EST'
        },
        'UNRATE': {
            'frequency': 'monthly',
            'release_pattern': 'first_friday',
            'release_time': '08:30',
            'timezone': 'EST'
        },

        # PMI - 月度，次月第一个工作日
        'NAPM': {
            'frequency': 'monthly',
            'release_day': '1',
            'release_time': '10:00',
            'timezone': 'EST'
        },

        # 工业产值 - 月度，次月中旬
        'INDPRO': {
            'frequency': 'monthly',
            'release_day': '15',
            'release_time': '09:15',
            'timezone': 'EST'
        },

        # 零售销售 - 月度，次月中旬
        'RSXFS': {
            'frequency': 'monthly',
            'release_day': '15',
            'release_time': '08:30',
            'timezone': 'EST'
        },

        # FOMC 利率决策 - 不定期（一年8次）
        'FEDFUNDS': {
            'frequency': 'irregular',
            'release_lag_days': 0,  # 当天发布
        },

        # 货币供应量 - 周度，周四下午
        'M1SL': {
            'frequency': 'weekly',
            'release_day_of_week': 'thursday',
            'release_time': '16:30',
            'timezone': 'EST'
        },
        'M2SL': {
            'frequency': 'weekly',
            'release_day_of_week': 'thursday',
            'release_time': '16:30',
            'timezone': 'EST'
        },

        # 国债收益率 - 日度，实时
        'DGS10': {
            'frequency': 'daily',
            'release_lag_days': 0,
        },
        'DGS2': {
            'frequency': 'daily',
            'release_lag_days': 0,
        },
    }

    def __init__(self):
        """初始化发布日历管理器"""
        pass

    def estimate_release_date(self,
                             indicator_code: str,
                             reference_date: str) -> Optional[datetime]:
        """
        根据参考日期估算发布日期

        Args:
            indicator_code: 指标代码
            reference_date: 数据所属期（参考日期）

        Returns:
            预计的发布日期
        """
        try:
            ref_date = pd.to_datetime(reference_date)

            if indicator_code not in self.RELEASE_SCHEDULE:
                # 如果没有配置，默认假设延迟1天
                logger.warning(f"指标 {indicator_code} 没有发布时间配置，使用默认延迟1天")
                return ref_date + timedelta(days=1)

            schedule = self.RELEASE_SCHEDULE[indicator_code]
            frequency = schedule.get('frequency', 'monthly')

            if frequency == 'daily':
                # 日度数据，当天或次日发布
                lag_days = schedule.get('release_lag_days', 0)
                return ref_date + timedelta(days=lag_days)

            elif frequency == 'weekly':
                # 周度数据
                day_of_week = schedule.get('release_day_of_week', 'thursday')
                # 找到参考日期后的第一个周四
                release_date = ref_date + timedelta(days=1)
                while release_date.strftime('%A').lower() != day_of_week:
                    release_date += timedelta(days=1)
                return release_date

            elif frequency == 'monthly':
                # 月度数据，通常在次月的某天发布
                release_day = schedule.get('release_day', '15')
                release_month = ref_date + pd.DateOffset(months=1)
                release_date = release_month.replace(day=int(release_day))

                # 如果发布日是周末，顺延到下一个工作日
                if release_date.strftime('%A') in ['Saturday', 'Sunday']:
                    while release_date.strftime('%A') in ['Saturday', 'Sunday']:
                        release_date += timedelta(days=1)

                return release_date

            elif frequency == 'quarterly':
                # 季度数据
                lag_days = schedule.get('release_lag_days', 30)
                return ref_date + timedelta(days=lag_days)

            elif frequency == 'irregular':
                # 不定期数据（如FOMC会议）
                return ref_date  # 简化处理，假设当天发布

            else:
                # 默认延迟1天
                return ref_date + timedelta(days=1)

        except Exception as e:
            logger.error(f"估算发布日期失败: {str(e)}")
            return None

    def get_release_dates(self,
                         indicator_code: str,
                         start_date: str,
                         end_date: str) -> pd.DataFrame:
        """
        获取指定指标在日期范围内的发布日期

        Args:
            indicator_code: 指标代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含参考日期和发布日期的 DataFrame
        """
        try:
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')

            release_dates = []
            for ref_date in date_range:
                release_date = self.estimate_release_date(indicator_code, ref_date)
                if release_date:
                    release_dates.append({
                        'indicator_code': indicator_code,
                        'reference_date': ref_date,
                        'release_date': release_date
                    })

            return pd.DataFrame(release_dates)

        except Exception as e:
            logger.error(f"获取发布日期失败: {str(e)}")
            return pd.DataFrame()

    def save_release_calendar_to_db(self,
                                    df: pd.DataFrame) -> bool:
        """
        将发布日历保存到数据库

        Args:
            df: 包含发布日历的 DataFrame

        Returns:
            是否成功保存
        """
        try:
            connection = pymysql.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DATABASE_NAME,
                charset=DB_CONFIG['charset']
            )

            cursor = connection.cursor()

            # 插入数据（忽略重复）
            insert_sql = """
                INSERT IGNORE INTO release_calendar
                (indicator_code, indicator_name, country, release_date, reference_date, frequency)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            for _, row in df.iterrows():
                indicator_code = row.get('indicator_code', '')
                indicator_name = row.get('indicator_name', indicator_code)
                release_date = row.get('release_date')
                reference_date = row.get('reference_date', release_date)
                frequency = row.get('frequency', 'unknown')

                if release_date:
                    cursor.execute(insert_sql, (
                        indicator_code,
                        indicator_name,
                        'US',
                        release_date,
                        reference_date,
                        frequency
                    ))

            connection.commit()
            cursor.close()
            connection.close()

            logger.info(f"成功保存 {len(df)} 条发布日历记录")
            return True

        except Exception as e:
            logger.error(f"保存发布日历失败: {str(e)}")
            return False

    def get_available_data_for_date(self,
                                    date: str,
                                    data_table_name: str = 'us_macro_data') -> pd.DataFrame:
        """
        获取在指定日期实际可观测的数据（避免未来函数）

        Args:
            date: 查询日期
            data_table_name: 数据表名

        Returns:
            在该日期可观测的数据
        """
        try:
            connection = pymysql.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DATABASE_NAME,
                charset=DB_CONFIG['charset']
            )

            query = f"""
                SELECT d.*
                FROM {data_table_name} d
                LEFT JOIN release_calendar r
                    ON d.indicator_code = r.indicator_code
                    AND d.date = r.reference_date
                WHERE d.date <= '{date}'
                AND (r.release_date IS NULL OR r.release_date <= '{date}')
                ORDER BY d.indicator_code, d.date DESC
            """

            df = pd.read_sql(query, connection)

            # 对每个指标，只取最新的那条
            if not df.empty:
                df = df.groupby('indicator_code').first().reset_index()

            connection.close()

            logger.info(f"在 {date} 可观测的数据: {len(df)} 条")
            return df

        except Exception as e:
            logger.error(f"获取可观测数据失败: {str(e)}")
            return pd.DataFrame()


# 测试代码
if __name__ == "__main__":
    calendar = FREDReleaseCalendar()

    # 测试估算发布日期
    print("\n测试估算 CPI 发布日期:")
    release_date = calendar.estimate_release_date('CPIAUCSL', '2024-01-01')
    print(f"2024年1月CPI的预计发布日期: {release_date}")

    print("\n测试估算 GDP 发布日期:")
    release_date = calendar.estimate_release_date('GDP', '2024-03-31')
    print(f"2024年Q1 GDP的预计发布日期: {release_date}")

    # 测试获取发布日期范围
    print("\n测试获取非农就业的发布日期:")
    release_dates = calendar.get_release_dates('PAYEMS', '2024-01-01', '2024-03-31')
    if not release_dates.empty:
        print(release_dates.head(10))
