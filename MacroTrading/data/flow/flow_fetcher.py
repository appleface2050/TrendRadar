"""
资金流数据获取器

获取中国市场的资金流数据，包括：
1. 北向/南向资金流
2. VIX指数
3. 美元指数
4. 美债收益率
5. AH溢价指数
6. 中美利差

数据源：
- Tushare: 北向/南向资金、AH溢价
- FRED: VIX、美元指数、美债收益率
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False
    print("Warning: tushare not installed. Install with: pip install tushare")

try:
    import pandas_datareader.data as web
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False
    print("Warning: pandas-datareader not installed. Install with: pip install pandas-datareader")


class FlowDataFetcher:
    """资金流数据获取器"""

    def __init__(self, tushare_token=None, fred_key=None):
        """
        初始化资金流数据获取器

        Parameters:
        -----------
        tushare_token : str, optional
            Tushare API token
        fred_key : str, optional
            FRED API key
        """
        self.tushare_token = tushare_token
        self.fred_key = fred_key

        # 初始化Tushare
        if TUSHARE_AVAILABLE and self.tushare_token:
            self.pro = ts.pro_api(self.tushare_token)
        else:
            self.pro = None
            print("Tushare not available or no token provided")

        # 设置FRED API key
        if FRED_AVAILABLE and self.fred_key:
            import os
            os.environ['FRED_API_KEY'] = self.fred_key

    def get_northbound_flow(self, start_date, end_date):
        """
        获取北向资金流数据

        Parameters:
        -----------
        start_date : str
            开始日期，格式：YYYYMMDD
        end_date : str
            结束日期，格式：YYYYMMDD

        Returns:
        --------
        DataFrame
            北向资金流数据
        """
        if not self.pro:
            print("Error: Tushare not initialized")
            return None

        try:
            # 获取沪股通和深股通资金流
            df = self.pro.moneyflow_hsgt(start_date=start_date, end_date=end_date)

            if df is not None and len(df) > 0:
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df = df.sort_values('trade_date')

                # 计算净流入
                df['net_flow_north'] = df['ggt_ss'] + df['ggt_sz']  # 沪股通+深股通

                return df

        except Exception as e:
            print(f"Error fetching northbound flow: {e}")

        return None

    def get_southbound_flow(self, start_date, end_date):
        """
        获取南向资金流数据

        Parameters:
        -----------
        start_date : str
            开始日期，格式：YYYYMMDD
        end_date : str
            结束日期，格式：YYYYMMDD

        Returns:
        --------
        DataFrame
            南向资金流数据
        """
        if not self.pro:
            print("Error: Tushare not initialized")
            return None

        try:
            # 获取港股通资金流
            df = self.pro.moneyflow_hsgt(start_date=start_date, end_date=end_date)

            if df is not None and len(df) > 0:
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df = df.sort_values('trade_date')

                # 计算净流入
                df['net_flow_south'] = df['hgt']  # 港股通

                return df

        except Exception as e:
            print(f"Error fetching southbound flow: {e}")

        return None

    def get_vix(self, start_date, end_date):
        """
        获取VIX指数数据

        Parameters:
        -----------
        start_date : str
            开始日期，格式：YYYY-MM-DD
        end_date : str
            结束日期，格式：YYYY-MM-DD

        Returns:
        --------
        DataFrame
            VIX指数数据
        """
        if not FRED_AVAILABLE:
            print("Error: pandas-datareader not available")
            return None

        try:
            # VIX代码: VIXCLS
            df = web.DataReader('VIXCLS', 'fred', start_date, end_date)
            df = df.dropna()
            df.columns = ['vix']
            df.index.name = 'date'

            return df

        except Exception as e:
            print(f"Error fetching VIX: {e}")

        return None

    def get_dxy(self, start_date, end_date):
        """
        获取美元指数数据

        Parameters:
        -----------
        start_date : str
            开始日期，格式：YYYY-MM-DD
        end_date : str
            结束日期，格式：YYYY-MM-DD

        Returns:
        --------
        DataFrame
            美元指数数据
        """
        if not FRED_AVAILABLE:
            print("Error: pandas-datareader not available")
            return None

        try:
            # 美元指数代码: DTWEXBGS
            df = web.DataReader('DTWEXBGS', 'fred', start_date, end_date)
            df = df.dropna()
            df.columns = ['dxy']
            df.index.name = 'date'

            return df

        except Exception as e:
            print(f"Error fetching DXY: {e}")

        return None

    def get_us_treasury_yield(self, start_date, end_date, maturity='10y', use_local=True):
        """
        获取美国国债收益率

        Parameters:
        -----------
        start_date : str
            开始日期，格式：YYYY-MM-DD
        end_date : str
            结束日期，格式：YYYY-MM-DD
        maturity : str
            期限：'1y', '2y', '3y', '5y', '10y', '30y'
        use_local : bool
            优先使用本地CSV文件

        Returns:
        --------
        DataFrame
            美国国债收益率数据
        """
        # 期限代码映射
        maturity_codes = {
            '1y': 'DGS1',
            '2y': 'DGS2',
            '3y': 'DGS3',
            '5y': 'DGS5',
            '10y': 'DGS10',
            '30y': 'DGS30'
        }

        code = maturity_codes.get(maturity.lower(), 'DGS10')

        # 优先使用本地CSV文件
        if use_local:
            try:
                # 本地文件路径
                local_file = '/home/shang/git/Indeptrader/Macroeconomic/data/fred_treasury_yield/treasury_yield_daily.csv'

                # 读取CSV
                df = pd.read_csv(local_file)
                df['DATE'] = pd.to_datetime(df['DATE'])
                df = df.set_index('DATE')

                # 筛选日期范围
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df.index >= start_dt) & (df.index <= end_dt)]

                # 提取指定期限的数据
                if code in df.columns:
                    df = df[[code]].copy()
                    df.columns = [f'us_treasury_{maturity}']
                    df = df.dropna()
                    df.index.name = 'date'

                    print(f"✓ 从本地文件获取{maturity}国债收益率：{len(df)}条记录")
                    return df
                else:
                    print(f"Warning: {code} not in local file")

            except Exception as e:
                print(f"Warning: 读取本地文件失败: {e}")

        # 如果本地文件失败，尝试FRED API
        if not FRED_AVAILABLE:
            print("Error: pandas-datareader not available and local file failed")
            return None

        try:
            df = web.DataReader(code, 'fred', start_date, end_date)
            df = df.dropna()
            df.columns = [f'us_treasury_{maturity}']
            df.index.name = 'date'

            return df

        except Exception as e:
            print(f"Error fetching US treasury yield: {e}")

        return None

    def get_ah_premium(self, start_date, end_date):
        """
        获取AH溢价指数

        Parameters:
        -----------
        start_date : str
            开始日期，格式：YYYYMMDD
        end_date : str
            结束日期，格式：YYYYMMDD

        Returns:
        --------
        DataFrame
            AH溢价指数数据
        """
        if not self.pro:
            print("Error: Tushare not initialized")
            return None

        try:
            # 获取AH溢价指数
            df = self.pro.index_daily(ts_code='930001.SI',
                                     start_date=start_date,
                                     end_date=end_date)

            if df is not None and len(df) > 0:
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df = df[['trade_date', 'close']]
                df.columns = ['date', 'ah_premium']
                df = df.set_index('date')

                return df

        except Exception as e:
            print(f"Error fetching AH premium: {e}")

        return None

    def get_china_interest_rate(self, start_date, end_date):
        """
        获取中国利率数据（Shibor）

        Parameters:
        -----------
        start_date : str
            开始日期，格式：YYYYMMDD
        end_date : str
            结束日期，格式：YYYYMMDD

        Returns:
        --------
        DataFrame
            中国利率数据
        """
        if not self.pro:
            print("Error: Tushare not initialized")
            return None

        try:
            # 获取Shibor利率数据
            df = self.pro.shibor(start_date=start_date, end_date=end_date)

            if df is not None and len(df) > 0:
                df['date'] = pd.to_datetime(df['date'])
                df = df[['date', 'on', '1w', '2w', '1m', '3m', '6m', '9m', '1y']]
                df = df.set_index('date')

                return df

        except Exception as e:
            print(f"Error fetching China interest rate: {e}")

        return None

    def calculate_real_rate_diff(self, start_date, end_date):
        """
        计算中美实际利差

        Parameters:
        -----------
        start_date : str
            开始日期，格式：YYYY-MM-DD
        end_date : str
            结束日期，格式：YYYY-MM-DD

        Returns:
        --------
        DataFrame
            中美实际利差数据
        """
        # 获取美国10年期国债收益率
        us_yield = self.get_us_treasury_yield(start_date, end_date, '10y')

        # 获取中国Shibor 3个月利率
        tushare_start = start_date.replace('-', '')
        tushare_end = end_date.replace('-', '')
        china_rate = self.get_china_interest_rate(tushare_start, tushare_end)

        if us_yield is None or china_rate is None:
            return None

        # 统一日期格式
        us_yield.index = pd.to_datetime(us_yield.index)
        china_rate.index = pd.to_datetime(china_rate.index)

        # 合并数据
        df = pd.merge(us_yield, china_rate[['3m']],
                     left_index=True, right_index=True,
                     how='inner')

        # 计算利差（中国利率 - 美国利率）
        df['rate_diff'] = df['3m'] - df['us_treasury_10y']
        df = df[['rate_diff']]

        return df

    def fetch_all_flow_data(self, start_date, end_date):
        """
        获取所有资金流相关数据

        Parameters:
        -----------
        start_date : str
            开始日期，格式：YYYY-MM-DD
        end_date : str
            结束日期，格式：YYYY-MM-DD

        Returns:
        --------
        dict
            包含所有资金流数据的字典
        """
        print("开始获取资金流数据...")

        result = {}

        # 北向资金流
        tushare_start = start_date.replace('-', '')
        tushare_end = end_date.replace('-', '')
        northbound = self.get_northbound_flow(tushare_start, tushare_end)
        if northbound is not None:
            result['northbound_flow'] = northbound
            print(f"✓ 北向资金流数据获取成功：{len(northbound)}条记录")

        # 南向资金流
        southbound = self.get_southbound_flow(tushare_start, tushare_end)
        if southbound is not None:
            result['southbound_flow'] = southbound
            print(f"✓ 南向资金流数据获取成功：{len(southbound)}条记录")

        # VIX指数
        vix = self.get_vix(start_date, end_date)
        if vix is not None:
            result['vix'] = vix
            print(f"✓ VIX指数数据获取成功：{len(vix)}条记录")

        # 美元指数
        dxy = self.get_dxy(start_date, end_date)
        if dxy is not None:
            result['dxy'] = dxy
            print(f"✓ 美元指数数据获取成功：{len(dxy)}条记录")

        # 美国国债收益率
        us_yield = self.get_us_treasury_yield(start_date, end_date, '10y')
        if us_yield is not None:
            result['us_treasury_10y'] = us_yield
            print(f"✓ 美国10年期国债收益率数据获取成功：{len(us_yield)}条记录")

        # AH溢价指数
        ah_premium = self.get_ah_premium(tushare_start, tushare_end)
        if ah_premium is not None:
            result['ah_premium'] = ah_premium
            print(f"✓ AH溢价指数数据获取成功：{len(ah_premium)}条记录")

        # 中美实际利差
        rate_diff = self.calculate_real_rate_diff(start_date, end_date)
        if rate_diff is not None:
            result['rate_diff'] = rate_diff
            print(f"✓ 中美实际利差数据获取成功：{len(rate_diff)}条记录")

        print("\n所有资金流数据获取完成！")

        return result

    def export_to_csv(self, data_dict, output_dir='data/csv/'):
        """
        将数据导出为CSV文件

        Parameters:
        -----------
        data_dict : dict
            包含所有数据的字典
        output_dir : str
            输出目录
        """
        import os

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"\n开始导出数据到 {output_dir}...")

        for key, df in data_dict.items():
            if df is not None and len(df) > 0:
                file_path = os.path.join(output_dir, f'{key}.csv')
                df.to_csv(file_path, encoding='utf-8-sig')
                print(f"✓ 导出成功：{file_path} ({len(df)}条记录)")

        print("\n所有数据导出完成！")


# 测试代码
if __name__ == "__main__":
    from configs.db_config import get_confidential_config

    config = get_confidential_config()

    fetcher = FlowDataFetcher(
        tushare_token=config.get('TUSHARE_DataApi__token'),
        fred_key=config.get('FRED_API_Key')
    )

    # 测试获取最近1年的数据
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    print(f"测试获取资金流数据：{start_date} 至 {end_date}")
    print("=" * 80)

    data = fetcher.fetch_all_flow_data(start_date, end_date)

    # 导出CSV
    if data:
        fetcher.export_to_csv(data)

        # 显示数据统计
        print("\n数据统计：")
        print("=" * 80)
        for key, df in data.items():
            if df is not None and len(df) > 0:
                print(f"\n{key}:")
                print(f"  时间范围：{df.index.min()} 至 {df.index.max()}")
                print(f"  记录数：{len(df)}")
                print(f"  数据预览：\n{df.head()}")
