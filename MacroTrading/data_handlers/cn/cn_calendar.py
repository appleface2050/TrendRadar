"""
中国宏观数据发布日历
记录中国宏观数据的发布时间，考虑春节等中国特色因素
"""
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from chinese_calendar import is_workday  # 需要安装 chinese_calendar 库
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


class CNReleaseCalendar:
    """中国宏观数据发布日历管理器"""

    # 主要指标的发布时间规则（经验数据）
    # 中国数据发布特点：
    # 1. 月度数据通常在次月中旬发布
    # 2. 季度数据（GDP）在次月中旬发布
    # 3. 需要考虑春节、国庆等长假影响
    # 4. 周末发布会顺延到工作日

    RELEASE_SCHEDULE = {
        # GDP - 季度，季度结束后次月中旬发布
        'GDP': {
            'frequency': 'quarterly',
            'release_day': '15',  # 次月15号左右
            'release_time': '10:00',
            'timezone': 'CST'
        },

        # CPI - 月度，次月9日左右
        'CPI': {
            'frequency': 'monthly',
            'release_day': '9',
            'release_time': '09:30',
            'timezone': 'CST'
        },
        'CPI_PP': {
            'frequency': 'monthly',
            'release_day': '9',
            'release_time': '09:30',
            'timezone': 'CST'
        },

        # PPI - 月度，与CPI同时发布
        'PPI': {
            'frequency': 'monthly',
            'release_day': '9',
            'release_time': '09:30',
            'timezone': 'CST'
        },
        'PPI_PP': {
            'frequency': 'monthly',
            'release_day': '9',
            'release_time': '09:30',
            'timezone': 'CST'
        },

        # 货币供应量 - 月度，次月10-15日
        'M0': {
            'frequency': 'monthly',
            'release_day': '10',
            'release_time': '15:00',
            'timezone': 'CST'
        },
        'M1': {
            'frequency': 'monthly',
            'release_day': '10',
            'release_time': '15:00',
            'timezone': 'CST'
        },
        'M2': {
            'frequency': 'monthly',
            'release_day': '10',
            'release_time': '15:00',
            'timezone': 'CST'
        },

        # PMI - 月度，次月首日（通常很早）
        'PMI': {
            'frequency': 'monthly',
            'release_day': '1',
            'release_time': '09:00',
            'timezone': 'CST'
        },
        'NON_MANPMI': {
            'frequency': 'monthly',
            'release_day': '1',
            'release_time': '09:00',
            'timezone': 'CST'
        },

        # 社会融资规模 - 月度，次月10-15日
        'SHIBOR': {
            'frequency': 'daily',
            'release_lag_days': 0,  # 当日发布
        },
        'SHIBORON': {
            'frequency': 'daily',
            'release_lag_days': 0,
        },
        'SHIBOR1W': {
            'frequency': 'daily',
            'release_lag_days': 0,
        },

        # 进出口数据 - 月度，次月7日左右
        'TRADE': {
            'frequency': 'monthly',
            'release_day': '7',
            'release_time': '10:00',
            'timezone': 'CST'
        },

        # 固定资产投资 - 月度，次月14日左右
        'FI_INV': {
            'frequency': 'monthly',
            'release_day': '14',
            'release_time': '10:00',
            'timezone': 'CST'
        },

        # 工业增加值 - 月度，次月14日左右
        'FI_IND': {
            'frequency': 'monthly',
            'release_day': '14',
            'release_time': '10:00',
            'timezone': 'CST'
        },

        # 社会消费品零售总额 - 月度，次月14日左右
        'RETAIL': {
            'frequency': 'monthly',
            'release_day': '14',
            'release_time': '10:00',
            'timezone': 'CST'
        },
    }

    def __init__(self):
        """初始化发布日历管理器"""
        pass

    def _adjust_for_holidays(self, date: datetime) -> datetime:
        """
        调整发布日期，考虑中国节假日和周末

        Args:
            date: 原始发布日期

        Returns:
            调整后的发布日期
        """
        try:
            # 如果是周末，顺延到下一个工作日
            max_attempts = 10  # 最多尝试10天
            attempts = 0

            while attempts < max_attempts:
                date_str = date.strftime('%Y-%m-%d')

                try:
                    # 检查是否为工作日
                    if is_workday(date):
                        return date
                except:
                    # 如果 chinese_calendar 不可用，简单检查周末
                    if date.weekday() < 5:  # 0-4 是周一到周五
                        return date

                # 如果不是工作日，顺延一天
                date += timedelta(days=1)
                attempts += 1

            return date

        except Exception as e:
            logger.warning(f"调整日期失败: {str(e)}")
            return date

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
                # 如果没有配置，默认假设延迟15天（月度数据平均）
                logger.warning(f"指标 {indicator_code} 没有发布时间配置，使用默认延迟15天")
                return self._adjust_for_holidays(ref_date + timedelta(days=15))

            schedule = self.RELEASE_SCHEDULE[indicator_code]
            frequency = schedule.get('frequency', 'monthly')

            if frequency == 'daily':
                # 日度数据，当天发布
                lag_days = schedule.get('release_lag_days', 0)
                return ref_date + timedelta(days=lag_days)

            elif frequency == 'weekly':
                # 周度数据，假设延迟1天
                return self._adjust_for_holidays(ref_date + timedelta(days=1))

            elif frequency == 'monthly':
                # 月度数据，通常在次月的某天发布
                release_day = schedule.get('release_day', '15')
                release_month = ref_date + pd.DateOffset(months=1)
                release_date = release_month.replace(day=int(release_day))

                # 调整节假日
                return self._adjust_for_holidays(release_date)

            elif frequency == 'quarterly':
                # 季度数据，在次月发布
                release_day = schedule.get('release_day', '15')
                release_month = ref_date + pd.DateOffset(months=1)
                release_date = release_month.replace(day=int(release_day))

                # 调整节假日
                return self._adjust_for_holidays(release_date)

            else:
                # 默认延迟15天
                return self._adjust_for_holidays(ref_date + timedelta(days=15))

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
                        'CN',
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
                                    data_table_name: str = 'cn_macro_data') -> pd.DataFrame:
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
    calendar = CNReleaseCalendar()

    # 测试估算发布日期
    print("\n测试估算 CPI 发布日期:")
    release_date = calendar.estimate_release_date('CPI', '2024-01-01')
    print(f"2024年1月CPI的预计发布日期: {release_date}")

    print("\n测试估算 GDP 发布日期:")
    release_date = calendar.estimate_release_date('GDP', '2024-03-31')
    print(f"2024年Q1 GDP的预计发布日期: {release_date}")

    print("\n测试估算 PMI 发布日期:")
    release_date = calendar.estimate_release_date('PMI', '2024-01-31')
    print(f"2024年1月PMI的预计发布日期: {release_date}")
