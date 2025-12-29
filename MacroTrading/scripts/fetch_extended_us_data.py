"""
获取完整历史的美国宏观数据
从FRED API获取所有可用的宏观经济指标，从最早可获得的数据开始
"""
import pandas as pd
import pandas_datareader.data as web
from datetime import datetime
import time
import logging
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from configs.db_config import FRED_API_KEY

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ExtendedUSDataFetcher:
    """扩展的美国数据获取器 - 获取所有可用历史数据"""

    # 扩展的宏观经济指标列表
    EXTENDED_INDICATORS = {
        # ===== GDP =====
        'GDP': 'Gross Domestic Product',
        'GDPC1': 'Real Gross Domestic Product',
        'GDPPOT': 'Real Potential Gross Domestic Product',
        'GDPCVIC': 'Real Gross Domestic Product, 3 Decimal',
        'NYGNPQ188S': 'Gross National Product',
        'GNP': 'Gross National Product',

        # ===== GDP Components =====
        'PCEC': 'Personal Consumption Expenditures',
        'FPCEC': 'Real Personal Consumption Expenditures',
        'A191RO1Q225SBEA': 'Gross Private Domestic Investment',
        'GPDIC1': 'Gross Private Domestic Investment',
        'FRED': 'Federal Government Current Expenditures',
        'FGEXPND': 'Federal Government Current Expenditures',
        'A191RO1Q225SBEA': 'Gross Private Domestic Investment',

        # ===== Inflation =====
        'CPIAUCSL': 'Consumer Price Index for All Urban Consumers: All Items',
        'CPILFESL': 'Core CPI (excluding food and energy)',
        'CPIAUCSL': 'CPI All Urban Consumers',
        'PCEPI': 'Personal Consumption Expenditures Price Index',
        'PCEPI': 'PCE Price Index',
        'DFEDTARU': 'Terminal Rate (Implied by Fed Funds Futures)',
        'T10YIE': '10-Year Breakeven Inflation Rate',
        'CORESTICKM159SFRBATL': 'Core CPI less Food & Energy',

        # ===== Employment =====
        'UNRATE': 'Unemployment Rate',
        'PAYEMS': 'All Employees, Nonfarm Payrolls',
        'CIVPART': 'Labor Force Participation Rate',
        'EMRATIO': 'Employment-Population Ratio',
        'MANEMP': 'All Employees, Manufacturing',
        'CES0600000007': 'Average Hourly Earnings of Production and Nonsupervisory Employees',
        'UNRATE': 'Unemployment Rate',
        'NROUST': 'Nonfarm Business Sector: Real Output Per Hour',
        'PRS85006012': 'Labor Force Participation Rate - Men',
        'LNS11300012': 'Labor Force Participation Rate - Women',

        # ===== PMI =====
        'NAPM': 'ISM Manufacturing: PMI Composite Index',
        'NAPMEI': 'ISM Manufacturing: Employment Index',
        'NAPMPMI': 'ISM Manufacturing: Production Index',
        'MANEMP': 'All Employees, Manufacturing',
        'USREC': 'NBER Recession Indicator',

        # ===== Industrial Production =====
        'INDPRO': 'Industrial Production Index',
        'MCUMFN': 'Capacity Utilization: Manufacturing (SIC)',
        'DGORDER': 'Manufacturer New Orders: Durable Goods',
        'AMDNO': 'New Orders for Durable Goods',
        'AMDMUO': 'New Orders for Nondefense Capital Goods',

        # ===== Retail Sales =====
        'RSXFS': 'Retail and Food Services Sales (Excluding Food Services)',
        'MRTSSM44S72BSA': 'Retail Sales: Retail Trade',
        'RSXFS': 'Retail Sales Excluding Food Services',

        # ===== Housing =====
        'HOUST': 'Housing Starts: Total: New Privately Owned Housing Units Started',
        'PERMIT': 'New Private Housing Units Authorized by Building Permits',
        'MSACSR': 'Monthly Supply of Houses in the United States',
        'MSPNHSUS': 'New One-Family Houses Sold',
        'MORTGAGE30US': '30-Year Fixed Rate Mortgage Average',

        # ===== Consumer Confidence =====
        'UMCSENT': 'University of Michigan: Consumer Sentiment',
        'CSCICP03USM665S': 'Composite Leading Indicators: Consumer Confidence Index',
        'CCIACCS': 'Consumer Confidence Index',

        # ===== Interest Rates & Yields =====
        'FEDFUNDS': 'Federal Funds Effective Rate',
        'DGS10': 'Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity',
        'DGS2': 'Market Yield on U.S. Treasury Securities at 2-Year Constant Maturity',
        'DGS3MO': '3-Month Treasury Bill Secondary Market Rate',
        'DGS5': '5-Year Treasury Constant Maturity Rate',
        'DGS30': '30-Year Treasury Constant Maturity Rate',
        'T10Y2Y': '10-Year Treasury Constant Maturity Minus 2-Year',
        'T10Y3M': '10-Year Treasury Constant Maturity Minus 3-Month',
        'DGS1': '1-Year Treasury Constant Maturity Rate',
        'DGS7': '7-Year Treasury Constant Maturity Rate',
        'DAAA': 'Moody\'s Seasoned Aaa Corporate Bond Yield',
        'DBAA': 'Moody\'s Seasoned Baa Corporate Bond Yield',
        'BAA10Y': 'Moody\'s Seasoned Baa Corporate Bond Yield Minus 10-Year Treasury',

        # ===== Money Supply =====
        'M1SL': 'M1 Money Supply',
        'M2SL': 'M2 Money Supply',
        'M1V': 'M1 Money Velocity',
        'M2V': 'M2 Money Velocity',
        'BOGMBASE': 'Monetary Base; Total',
        'RESPPANWW': 'Total Reserves of Depository Institutions',
        'WM2NS': 'M2 Money Stock',

        # ===== Fiscal =====
        'FYFSGDA188S': 'Federal Surplus or Deficit',
        'GFDEBTN': 'Federal Debt: Total Public Debt',
        'FYFRGDA188S': 'Federal Government Current Expenditures',

        # ===== Stock Market =====
        'SP500': 'S&P 500',
        'WILL5000IND': 'Wilshire 5000 Total Market Index',
        'DJIA': 'Dow Jones Industrial Average',
        'NASDAQCOM': 'NASDAQ Composite Index',
        'VIXCLS': 'CBOE Volatility Index: VIX',

        # ===== Exchange Rates =====
        'DEXUSEU': 'U.S. / Euro Exchange Rate',
        'DEXJPUS': 'Japan / U.S. Foreign Exchange Rate',
        'DEXCHUS': 'China / U.S. Foreign Exchange Rate',
        'DEXUSUK': 'U.S. / U.K. Exchange Rate',
        'DTWEXBGS': 'Trade Weighted U.S. Dollar Index: Broad',
        'DTWEXAFEGS': 'Trade Weighted U.S. Dollar Index: Against Major Currencies',

        # ===== Commodities =====
        'DCOILWTICO': 'Crude Oil Prices: West Texas Intermediate',
        'GASPRM': 'Regular Gasoline Prices',

        # ===== Credit =====
        'BAMLCC0A0CMTRIV': 'Bank of America Merrill Lynch US High Yield Index',
        'BAA10Y': 'Moody\'s Baa Corporate Bond Minus 10-Year Treasury',
        'DAAA': 'Moody\'s Seasoned Aaa Corporate Bond Yield',

        # ===== Leading Indicators =====
        'USSLIND': 'Leading Index for the United States',
        'USSCONF': 'Leading Indicators: Consumer Confidence Index',
        'AWHMANAG': 'Average Weekly Hours of Production and Nonsupervisory Employees',

        # ===== International Trade =====
        'BOPGSTB': 'U.S. Trade in Goods and Services',
        'EXPGS': 'Exports of Goods and Services',
        'IMPGS': 'Imports of Goods and Services',
        'NETFI': 'Net Foreign Factor Income',

        # ===== Productivity =====
        'NONACCCBO': 'Nonfarm Business Sector: Labor Productivity',
        'OPHNFB': 'Nonfarm Business Sector: Real Output Per Hour',
        'PRS85006012': 'Labor Force Participation Rate - Men',

        # ===== Wages & Income =====
        'CES0600000007': 'Average Hourly Earnings',
        'MEHOINUSA672N': 'Median Household Income',
        'DSPIC96': 'Real Disposable Personal Income',

        # ===== Corporate Profits =====
        'CP': 'Corporate Profits After Tax',
        'CPRAT': 'Corporate Profits After Tax with IVA and CCAdj',
        'CPAT': 'Corporate Profits After Tax',

        # ===== Consumption =====
        'PCECC96': 'Real Personal Consumption Expenditures',
        'DPCERL1Q225SBEA': 'Real Personal Consumption Expenditures: Durable Goods',
        'PCEVG': 'Personal Consumption Expenditures: Goods',
        'PCESV': 'Personal Consumption Expenditures: Services',
    }

    def __init__(self, api_key=None):
        self.api_key = api_key or FRED_API_KEY
        if self.api_key:
            # 设置API key到环境变量（pandas_datareader会从环境变量读取）
            import os
            os.environ['FRED_API_KEY'] = self.api_key
            logger.info(f"使用FRED API key: {self.api_key[:8]}...")
        else:
            logger.warning("未设置FRED API key，使用公开访问（可能有限制）")

    def fetch_indicator(self, code, start_date='1950-01-01'):
        """获取单个指标，从指定日期开始"""
        try:
            logger.info(f"正在获取 {code} ({self.EXTENDED_INDICATORS.get(code, code)})...")
            df = web.DataReader(code, 'fred', start_date)

            if df.empty:
                logger.warning(f"  {code} 没有数据")
                return None

            # 转换为长格式
            df = df.reset_index()
            df.columns = ['date', 'value']
            df['indicator_code'] = code
            df['indicator_name'] = self.EXTENDED_INDICATORS.get(code, code)

            logger.info(f"  ✓ 获取 {len(df)} 条数据，从 {df['date'].min()} 到 {df['date'].max()}")
            return df

        except Exception as e:
            logger.error(f"  ✗ {code} 获取失败: {str(e)}")
            return None

    def fetch_all_indicators(self, start_date='1950-01-01'):
        """获取所有指标"""
        logger.info("="*80)
        logger.info(f"开始获取美国宏观数据，起始日期：{start_date}")
        logger.info(f"共 {len(self.EXTENDED_INDICATORS)} 个指标")
        logger.info("="*80)

        all_data = []
        failed = []

        for i, (code, name) in enumerate(self.EXTENDED_INDICATORS.items(), 1):
            logger.info(f"\n[{i}/{len(self.EXTENDED_INDICATORS)}] 正在获取 {code}: {name}")

            df = self.fetch_indicator(code, start_date)
            if df is not None:
                all_data.append(df)

            # 避免请求过快
            time.sleep(0.5)

        # 合并所有数据
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            logger.info(f"\n{'='*80}")
            logger.info(f"成功获取 {len(all_data)}/{len(self.EXTENDED_INDICATORS)} 个指标")
            logger.info(f"总共 {len(result)} 条数据")
            logger.info(f"{'='*80}")

            # 保存
            output_path = project_root / 'data' / 'csv' / 'us_all_indicators_extended.csv'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"\n数据已保存到：{output_path}")

            # 统计
            print("\n数据概览：")
            print(f"  时间范围：{result['date'].min()} 至 {result['date'].max()}")
            print(f"  指标数量：{result['indicator_code'].nunique()}")
            print(f"  总数据点：{len(result)}")

            return result
        else:
            logger.error("没有获取到任何数据")
            return pd.DataFrame()


def main():
    """主函数"""
    # 设置API key
    api_key = FRED_API_KEY

    # 创建获取器
    fetcher = ExtendedUSDataFetcher(api_key=api_key)

    # 获取所有数据（从1950年开始）
    df = fetcher.fetch_all_indicators(start_date='1950-01-01')

    if not df.empty:
        print("\n✅ 数据获取完成！")
        print(f"\n指标列表：")
        for code, name in sorted(df.groupby('indicator_code')['indicator_name'].first().items()):
            print(f"  - {code}: {name}")
    else:
        print("\n❌ 数据获取失败")


if __name__ == '__main__':
    main()
