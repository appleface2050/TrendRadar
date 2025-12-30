"""
美国宏观数据获取器
从 FRED 获取美国宏观数据
"""
import pandas as pd
import pandas_datareader.data as web
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class USDataFetcher:
    """美国宏观数据获取器"""

    # FRED API 需要注册获取：https://fred.stlouisfed.org/docs/api/api_key.html
    # 可以从环境变量或配置文件中读取
    FRED_API_KEY = ''

    # 核心宏观经济指标定义
    MACRO_INDICATORS = {
        # GDP 相关
        'GDP': 'Gross Domestic Product',
        'GDPC1': 'Real Gross Domestic Product',
        'GDPPOT': 'Real Potential Gross Domestic Product',
        'NYGNPQ188S': 'Gross National Product',

        # 通胀指标
        'CPIAUCSL': 'Consumer Price Index for All Urban Consumers: All Items',
        'CPILFESL': 'Core CPI (excluding food and energy)',
        'PCEPI': 'Personal Consumption Expenditures Price Index',
        'DFEDTARU': 'Terminal Rate (Implied by Fed Funds Futures)',
        'FEDFUNDS': 'Federal Funds Effective Rate',

        # 就业市场
        'UNRATE': 'Unemployment Rate',
        'PAYEMS': 'All Employees, Nonfarm Payrolls',
        'CIVPART': 'Labor Force Participation Rate',

        # PMI
        'MANEMP': 'All Employees, Manufacturing',
        'NAPM': 'ISM Manufacturing: PMI Composite Index',
        'NAPMEI': 'ISM Manufacturing: Employment Index',

        # 工业产值
        'INDPRO': 'Industrial Production Index',
        'MCUMFN': 'Capacity Utilization: Manufacturing (SIC)',

        # 零售销售
        'RSXFS': 'Retail and Food Services Sales (Excluding Food Services)',
        'MRTSSM44S72BSA': 'Retail Sales: Retail Trade',

        # 住房市场
        'HOUST': 'Housing Starts: Total: New Privately Owned Housing Units Started',
        'PERMIT': 'New Private Housing Units Authorized by Building Permits',

        # 消费者信心
        'UMCSENT': 'University of Michigan: Consumer Sentiment',
        'CSCICP03USM665S': 'Composite Leading Indicators: Consumer Confidence Index',

        # 利率相关
        'DGS10': 'Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity',
        'DGS2': 'Market Yield on U.S. Treasury Securities at 2-Year Constant Maturity',
        'DGS3MO': '3-Month Treasury Bill Secondary Market Rate',
        'T10Y2Y': '10-Year Treasury Constant Maturity Minus 2-Year',
        'T10Y3M': '10-Year Treasury Constant Maturity Minus 3-Month',

        # 货币供应量
        'M1SL': 'M1 Money Supply',
        'M2SL': 'M2 Money Supply',
        'BOGMBASE': 'Monetary Base; Total',

        # 财政
        'FYFSGDA188S': 'Federal Surplus or Deficit',
        'GFDEBTN': 'Federal Debt: Total Public Debt',

        # 股票市场
        'SP500': 'S&P 500',
        'WILL5000IND': 'Wilshire 5000 Total Market Index',

        # 其他
        'DEXUSEU': 'U.S. / Euro Exchange Rate',
        'DEXJPUS': 'Japan / U.S. Foreign Exchange Rate',
        'DTWEXBGS': 'Trade Weighted U.S. Dollar Index: Broad',
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化数据获取器

        Args:
            api_key: FRED API key，如果为 None 则使用默认的
        """
        self.api_key = api_key or self.FRED_API_KEY
        if self.api_key:
            web.fred.FredReader.api_key = self.api_key

    def fetch_indicator(self, indicator_code: str,
                       start: Optional[str] = None,
                       end: Optional[str] = None) -> pd.DataFrame:
        """
        获取单个指标的数据

        Args:
            indicator_code: FRED 指标代码
            start: 开始日期，格式 'YYYY-MM-DD'
            end: 结束日期，格式 'YYYY-MM-DD'

        Returns:
            包含日期和值的 DataFrame
        """
        try:
            # 默认获取近 10 年的数据
            if not start:
                start = (datetime.now() - timedelta(days=365*10)).strftime('%Y-%m-%d')
            if not end:
                end = datetime.now().strftime('%Y-%m-%d')

            logger.info(f"正在获取指标 {indicator_code} 的数据 ({start} 至 {end})...")

            # 使用 pandas_datareader 获取数据
            df = web.DataReader(indicator_code, 'fred', start, end)

            if df.empty:
                logger.warning(f"指标 {indicator_code} 没有数据")
                return pd.DataFrame()

            # 重置索引，将日期变为列
            df = df.reset_index()
            df.columns = ['date', 'value']

            # 添加指标代码和名称
            df['indicator_code'] = indicator_code
            df['indicator_name'] = self.MACRO_INDICATORS.get(indicator_code, indicator_code)

            # 推断频率（简单的启发式方法）
            df['frequency'] = self._infer_frequency(df)

            logger.info(f"成功获取 {len(df)} 条数据")

            return df

        except Exception as e:
            logger.error(f"获取指标 {indicator_code} 失败: {str(e)}")
            return pd.DataFrame()

    def fetch_multiple_indicators(self,
                                  indicator_codes: List[str],
                                  start: Optional[str] = None,
                                  end: Optional[str] = None) -> pd.DataFrame:
        """
        获取多个指标的数据

        Args:
            indicator_codes: FRED 指标代码列表
            start: 开始日期
            end: 结束日期

        Returns:
            包含所有指标数据的 DataFrame
        """
        all_data = []

        for i, code in enumerate(indicator_codes):
            logger.info(f"进度: {i+1}/{len(indicator_codes)}")

            df = self.fetch_indicator(code, start, end)

            if not df.empty:
                all_data.append(df)

            # 避免请求过快
            time.sleep(0.5)

        if all_data:
            result_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"总共获取 {len(result_df)} 条数据")
            return result_df
        else:
            logger.warning("没有获取到任何数据")
            return pd.DataFrame()

    def fetch_all_core_indicators(self,
                                  start: Optional[str] = None,
                                  end: Optional[str] = None) -> pd.DataFrame:
        """
        获取所有核心宏观经济指标

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            包含所有核心指标数据的 DataFrame
        """
        # 核心指标列表（可以根据需要调整）
        core_indicators = [
            # GDP
            'GDP', 'GDPC1',

            # 通胀
            'CPIAUCSL', 'CPILFESL', 'PCEPI',

            # 就业
            'UNRATE', 'PAYEMS',

            # PMI
            'NAPM',

            # 工业产值
            'INDPRO', 'MCUMFN',

            # 零售销售
            'RSXFS',

            # 利率
            'FEDFUNDS', 'DGS10', 'DGS2', 'T10Y2Y', 'T10Y3M',

            # 货币供应量
            'M1SL', 'M2SL',
        ]

        return self.fetch_multiple_indicators(core_indicators, start, end)

    def _infer_frequency(self, df: pd.DataFrame) -> str:
        """
        推断数据频率

        Args:
            df: 包含日期和值的 DataFrame

        Returns:
            频率字符串 (d/w/m/q/ya)
        """
        if len(df) < 2:
            return 'unknown'

        # 计算日期间隔
        df['date'] = pd.to_datetime(df['date'])
        df_sorted = df.sort_values('date')
        intervals = df_sorted['date'].diff().dropna()

        if intervals.empty:
            return 'unknown'

        # 取最常见的间隔
        mode_interval = intervals.mode()[0]

        # 根据间隔判断频率
        if mode_interval.days <= 2:
            return 'd'  # 日度
        elif mode_interval.days <= 9:
            return 'w'  # 周度
        elif mode_interval.days <= 35:
            return 'm'  # 月度
        elif mode_interval.days <= 100:
            return 'q'  # 季度
        else:
            return 'ya'  # 年度

    def get_indicator_info(self) -> Dict[str, str]:
        """
        获取所有支持的指标信息

        Returns:
            指标代码到名称的映射字典
        """
        return self.MACRO_INDICATORS.copy()


# 测试代码
if __name__ == "__main__":
    fetcher = USDataFetcher()

    # 测试获取单个指标
    print("\n测试获取 GDP 数据:")
    gdp_data = fetcher.fetch_indicator('GDP', start='2020-01-01')
    if not gdp_data.empty:
        print(gdp_data.head())
        print(f"共 {len(gdp_data)} 条数据")

    # 测试获取多个核心指标
    print("\n测试获取核心指标:")
    core_data = fetcher.fetch_all_core_indicators(start='2023-01-01')
    if not core_data.empty:
        print(f"\n总共获取 {len(core_data)} 条数据")
        print("\n各指标数据量:")
        print(core_data['indicator_code'].value_counts())
