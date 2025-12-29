"""
中国宏观数据获取器
从 Tushare 获取中国宏观经济和金融数据
"""
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Optional
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.db_config import TUSHARE_TOKEN, TUSHARE_HTTP_URL

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CNDataFetcher:
    """中国宏观数据获取器"""

    # 核心宏观指标定义
    MACRO_INDICATORS = {
        # GDP 相关
        'gdp': {'name': '国内生产总值', 'freq': '季度'},
        'gdp_cython': {'name': 'GDP同比', 'freq': '季度'},

        # 通胀指标
        'cpi': {'name': '居民消费价格指数', 'freq': '月度'},
        'cpi_pp': {'name': 'CPI环比', 'freq': '月度'},
        'ppi': {'name': '工业品出厂价格指数', 'freq': '月度'},
        'ppi_pp': {'name': 'PPI环比', 'freq': '月度'},

        # 货币供应量
        'm2': {'name': 'M2货币供应量', 'freq': '月度'},
        'm1': {'name': 'M1货币供应量', 'freq': '月度'},
        'm0': {'name': 'M0货币供应量', 'freq': '月度'},

        # 社会融资
        'shibor': {'name': '上海银行间同业拆放利率', 'freq': '日度'},

        # PMI
        'pmi': {'name': '制造业PMI', 'freq': '月度'},
        'non_manpmi': {'name': '非制造业PMI', 'freq': '月度'},

        # 贸易
        'trade': {'name': '进出口贸易', 'freq': '月度'},

        # 固定资产投资
        'fi_inv': {'name': '固定资产投资', 'freq': '月度'},
        'fi_ind': {'name': '工业增加值', 'freq': '月度'},

        # 消费
        'retail': {'name': '社会消费品零售总额', 'freq': '月度'},

        # 利率
        'dr007': {'name': '银行间存款类金融机构7天期质押式回购利率', 'freq': '日度'},
    }

    def __init__(self, token: Optional[str] = None):
        """
        初始化数据获取器

        Args:
            token: Tushare API token，如果为 None 则从配置文件读取
        """
        self.token = token or TUSHARE_TOKEN

        if not self.token:
            logger.warning("未设置 Tushare token，某些功能可能受限")
            logger.warning("请在 confidential.json 中设置 TUSHARE_DataApi__token")
            self.pro = None
        else:
            try:
                # 使用标准方式初始化
                self.pro = ts.pro_api()

                # 设置特殊的 endpoint（按照 example 的方式）
                self.pro._DataApi__token = self.token
                self.pro._DataApi__http_url = TUSHARE_HTTP_URL

                logger.info("成功初始化 Tushare API（使用自定义 endpoint）")
                logger.info(f"API URL: {TUSHARE_HTTP_URL}")
            except Exception as e:
                logger.error(f"初始化 Tushare API 失败: {str(e)}")
                self.pro = None

    def fetch_gdp(self, start_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取 GDP 数据

        Args:
            start_date: 开始日期，格式 'YYYYMMDD'

        Returns:
            包含 GDP 数据的 DataFrame
        """
        try:
            if not self.pro:
                logger.error("Tushare API 未初始化")
                return pd.DataFrame()

            logger.info("正在获取 GDP 数据...")

            # 获取 GDP 数据
            df = self.pro.cn_gdp(start_date=start_date)

            if df.empty:
                logger.warning("GDP 数据为空")
                return pd.DataFrame()

            # 标准化列名
            df = df.rename(columns={
                'stat_year': 'year',
                'gdp': 'value',
            })

            # 添加指标信息
            df['indicator_code'] = 'GDP'
            df['indicator_name'] = '国内生产总值'

            # 构造日期（季度数据）
            if 'quarter' in df.columns:
                df['date'] = df['year'].astype(str) + 'Q' + df['quarter'].astype(str)
                df['frequency'] = 'q'
            else:
                df['date'] = df['year'].astype(str) + '-12-31'
                df['frequency'] = 'a'

            logger.info(f"成功获取 {len(df)} 条 GDP 数据")

            return df

        except Exception as e:
            logger.error(f"获取 GDP 数据失败: {str(e)}")
            return pd.DataFrame()

    def fetch_cpi(self, start_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取 CPI 数据

        Args:
            start_date: 开始日期

        Returns:
            包含 CPI 数据的 DataFrame
        """
        try:
            if not self.pro:
                logger.error("Tushare API 未初始化")
                return pd.DataFrame()

            logger.info("正在获取 CPI 数据...")

            # 获取 CPI 数据
            df = self.pro.cn_cpi(start_date=start_date)

            if df.empty:
                logger.warning("CPI 数据为空")
                return pd.DataFrame()

            # 标准化列名
            df['indicator_code'] = 'CPI'
            df['indicator_name'] = '居民消费价格指数'
            df['date'] = pd.to_datetime(df['month'], format='%Y%m')
            df['value'] = df['cpi_ci']  # 同比
            df['frequency'] = 'm'

            logger.info(f"成功获取 {len(df)} 条 CPI 数据")

            return df

        except Exception as e:
            logger.error(f"获取 CPI 数据失败: {str(e)}")
            return pd.DataFrame()

    def fetch_ppi(self, start_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取 PPI 数据

        Args:
            start_date: 开始日期

        Returns:
            包含 PPI 数据的 DataFrame
        """
        try:
            if not self.pro:
                logger.error("Tushare API 未初始化")
                return pd.DataFrame()

            logger.info("正在获取 PPI 数据...")

            # 获取 PPI 数据
            df = self.pro.cn_ppi(start_date=start_date)

            if df.empty:
                logger.warning("PPI 数据为空")
                return pd.DataFrame()

            # 标准化列名
            df['indicator_code'] = 'PPI'
            df['indicator_name'] = '工业品出厂价格指数'
            df['date'] = pd.to_datetime(df['month'], format='%Y%m')
            df['value'] = df['ppi_ci']  # 同比
            df['frequency'] = 'm'

            logger.info(f"成功获取 {len(df)} 条 PPI 数据")

            return df

        except Exception as e:
            logger.error(f"获取 PPI 数据失败: {str(e)}")
            return pd.DataFrame()

    def fetch_money_supply(self, start_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取货币供应量数据（M0, M1, M2）

        Args:
            start_date: 开始日期

        Returns:
            包含货币供应量数据的 DataFrame
        """
        try:
            if not self.pro:
                logger.error("Tushare API 未初始化")
                return pd.DataFrame()

            logger.info("正在获取货币供应量数据...")

            # 获取货币供应量数据
            df = self.pro.cn_m(start_date=start_date)

            if df.empty:
                logger.warning("货币供应量数据为空")
                return pd.DataFrame()

            # 处理 M2
            m2_df = df[['month', 'm2']].copy()
            m2_df['indicator_code'] = 'M2'
            m2_df['indicator_name'] = 'M2货币供应量'
            m2_df['date'] = pd.to_datetime(m2_df['month'], format='%Y%m')
            m2_df = m2_df.rename(columns={'m2': 'value'})
            m2_df['frequency'] = 'm'

            # 处理 M1
            m1_df = df[['month', 'm1']].copy()
            m1_df['indicator_code'] = 'M1'
            m1_df['indicator_name'] = 'M1货币供应量'
            m1_df['date'] = pd.to_datetime(m1_df['month'], format='%Y%m')
            m1_df = m1_df.rename(columns={'m1': 'value'})
            m1_df['frequency'] = 'm'

            # 处理 M0
            m0_df = df[['month', 'm0']].copy()
            m0_df['indicator_code'] = 'M0'
            m0_df['indicator_name'] = 'M0货币供应量'
            m0_df['date'] = pd.to_datetime(m0_df['month'], format='%Y%m')
            m0_df = m0_df.rename(columns={'m0': 'value'})
            m0_df['frequency'] = 'm'

            # 合并
            result_df = pd.concat([m2_df, m1_df, m0_df], ignore_index=True)

            logger.info(f"成功获取 {len(result_df)} 条货币供应量数据")

            return result_df

        except Exception as e:
            logger.error(f"获取货币供应量数据失败: {str(e)}")
            return pd.DataFrame()

    def fetch_pmi(self, start_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取 PMI 数据

        Args:
            start_date: 开始日期

        Returns:
            包含 PMI 数据的 DataFrame
        """
        try:
            if not self.pro:
                logger.error("Tushare API 未初始化")
                return pd.DataFrame()

            logger.info("正在获取 PMI 数据...")

            # 获取制造业 PMI
            df = self.pro.cn_pmi(start_date=start_date)

            if df.empty:
                logger.warning("PMI 数据为空")
                return pd.DataFrame()

            # 标准化列名
            df['indicator_code'] = 'PMI'
            df['indicator_name'] = '制造业PMI'
            df['date'] = pd.to_datetime(df['month'], format='%Y%m')
            df['value'] = df['pmi']
            df['frequency'] = 'm'

            logger.info(f"成功获取 {len(df)} 条 PMI 数据")

            return df

        except Exception as e:
            logger.error(f"获取 PMI 数据失败: {str(e)}")
            return pd.DataFrame()

    def fetch_shibor(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取 Shibor 利率数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含 Shibor 数据的 DataFrame
        """
        try:
            if not self.pro:
                logger.error("Tushare API 未初始化")
                return pd.DataFrame()

            logger.info("正在获取 Shibor 数据...")

            # 获取 Shibor 数据
            df = self.pro.shibor(start_date=start_date, end_date=end_date)

            if df.empty:
                logger.warning("Shibor 数据为空")
                return pd.DataFrame()

            # 选择隔夜和1周利率
            df_on = df[['date', 'on']].copy()
            df_on['indicator_code'] = 'SHIBORON'
            df_on['indicator_name'] = 'Shibor隔夜利率'
            df_on = df_on.rename(columns={'on': 'value'})
            df_on['frequency'] = 'd'

            df_1w = df[['date', '1w']].copy()
            df_1w['indicator_code'] = 'SHIBOR1W'
            df_1w['indicator_name'] = 'Shibor1周利率'
            df_1w = df_1w.rename(columns={'1w': 'value'})
            df_1w['frequency'] = 'd'

            # 合并
            result_df = pd.concat([df_on, df_1w], ignore_index=True)

            logger.info(f"成功获取 {len(result_df)} 条 Shibor 数据")

            return result_df

        except Exception as e:
            logger.error(f"获取 Shibor 数据失败: {str(e)}")
            return pd.DataFrame()

    def fetch_all_core_indicators(self,
                                  start_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取所有核心宏观指标

        Args:
            start_date: 开始日期，格式 'YYYYMMDD'

        Returns:
            包含所有核心指标数据的 DataFrame
        """
        all_data = []

        # GDP
        gdp_data = self.fetch_gdp(start_date=start_date)
        if not gdp_data.empty:
            all_data.append(gdp_data)
            time.sleep(0.5)

        # CPI
        cpi_data = self.fetch_cpi(start_date=start_date)
        if not cpi_data.empty:
            all_data.append(cpi_data)
            time.sleep(0.5)

        # PPI
        ppi_data = self.fetch_ppi(start_date=start_date)
        if not ppi_data.empty:
            all_data.append(ppi_data)
            time.sleep(0.5)

        # 货币供应量
        ms_data = self.fetch_money_supply(start_date=start_date)
        if not ms_data.empty:
            all_data.append(ms_data)
            time.sleep(0.5)

        # PMI
        pmi_data = self.fetch_pmi(start_date=start_date)
        if not pmi_data.empty:
            all_data.append(pmi_data)
            time.sleep(0.5)

        # Shibor（最近1年）
        shibor_start = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d') if not start_date else start_date
        shibor_data = self.fetch_shibor(start_date=shibor_start)
        if not shibor_data.empty:
            all_data.append(shibor_data)

        if all_data:
            result_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"总共获取 {len(result_df)} 条中国宏观数据")
            return result_df
        else:
            logger.warning("没有获取到任何数据")
            return pd.DataFrame()


# 测试代码
if __name__ == "__main__":
    # 注意：需要设置 Tushare token 才能正常使用
    fetcher = CNDataFetcher()

    if not fetcher.pro:
        print("\n错误: 未设置 Tushare API token")
        print("请在配置文件中设置 TUSHARE_TOKEN 或设置环境变量")
    else:
        # 测试获取 CPI 数据
        print("\n测试获取 CPI 数据:")
        cpi_data = fetcher.fetch_cpi(start_date='20230101')
        if not cpi_data.empty:
            print(cpi_data.head())
            print(f"共 {len(cpi_data)} 条数据")

        # 测试获取 PMI 数据
        print("\n测试获取 PMI 数据:")
        pmi_data = fetcher.fetch_pmi(start_date='20230101')
        if not pmi_data.empty:
            print(pmi_data.head())
            print(f"共 {len(pmi_data)} 条数据")
