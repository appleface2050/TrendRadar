"""
获取完整历史的中国宏观数据
从Tushare API获取所有可用的宏观经济指标，从最早可获得的数据开始
"""
import pandas as pd
import tushare as ts
from datetime import datetime
import time
import logging
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from configs.db_config import TUSHARE_TOKEN, TUSHARE_HTTP_URL

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ExtendedCNDataFetcher:
    """扩展的中国数据获取器 - 获取所有可用历史数据"""

    # 扩展的宏观指标列表
    EXTENDED_INDICATORS = {
        # ===== GDP =====
        'gdp': {'api': 'cn_gdp', 'name': '国内生产总值', 'freq': '季度'},
        'gdp_cython': {'api': 'cn_gdp', 'name': 'GDP同比', 'freq': '季度'},

        # ===== 通胀 =====
        'cpi': {'api': 'cn_cpi', 'name': 'CPI同比', 'freq': '月度'},
        'cpi_pp': {'api': 'cn_cpi_pp', 'name': 'CPI环比', 'freq': '月度'},
        'cpi_city': {'api': 'cn_cpi_city', 'name': '城市CPI', 'freq': '月度'},
        'ppi': {'api': 'cn_ppi', 'name': 'PPI同比', 'freq': '月度'},
        'ppi_pp': {'api': 'cn_ppi_pp', 'name': 'PPI环比', 'freq': '月度'},

        # ===== PMI =====
        'pmi': {'api': 'cn_pmi', 'name': '制造业PMI', 'freq': '月度'},
        'non_manpmi': {'api': 'cn_non_manpmi', 'name': '非制造业PMI', 'freq': '月度'},

        # ===== 就业 =====
        'emp': {'api': 'cn_emp', 'name': '就业人数', 'freq': '季度'},

        # ===== 固定资产投资 =====
        'fi_inv': {'api': 'cn_inv', 'name': '固定资产投资', 'freq': '月度'},
        'fi_inv_nd': {'api': 'cn_inv_nd', 'name': '固定资产投资（不含农户）', 'freq': '月度'},
        'faif': {'api': 'cn_faif', 'name': '固定资产投资完成额', 'freq': '月度'},

        # ===== 工业 =====
        'fi_ind': {'api': 'cn_ind', 'name': '工业增加值', 'freq': '月度'},
        'indpro': {'api': 'cn_indpro', 'name': '工业产值', 'freq': '月度'},

        # ===== 消费 =====
        'retail': {'api': 'cn_retail', 'name': '社会消费品零售总额', 'freq': '月度'},
        'retail_nd': {'api': 'cn_retail_nd', 'name': '社零（不含餐饮）', 'freq': '月度'},

        # ===== 对外贸易 =====
        'trade': {'api': 'cn_trade', 'name': '进出口贸易', 'freq': '月度'},
        'export': {'api': 'cn_export', 'name': '出口', 'freq': '月度'},
        'import': {'api': 'cn_import', 'name': '进口', 'freq': '月度'},
        'fes': {'api': 'cn_fes', 'name': '外汇储备', 'freq': '月度'},

        # ===== 货币供应量 =====
        'm2': {'api': 'cn_m', 'name': 'M2', 'freq': '月度'},
        'm1': {'api': 'cn_m', 'name': 'M1', 'freq': '月度'},
        'm0': {'api': 'cn_m', 'name': 'M0', 'freq': '月度'},

        # ===== 利率 =====
        'shibor': {'api': 'sh Shibor', 'name': 'Shibor', 'freq': '日度'},
        'dr007': {'api': 'cn_dr007', 'name': 'DR007', 'freq': '日度'},
        'lpr': {'api': 'cn_lpr', 'name': 'LPR', 'freq': '月度'},
        'lpr_1y': {'api': 'cn_lpr_1y', 'name': 'LPR_1年', 'freq': '月度'},

        # ===== 贷款和存款 =====
        'loan': {'api': 'cn_loan', 'name': '贷款', 'freq': '月度'},
        'depos': {'api': 'cn_depos', 'name': '存款', 'freq': '月度'},

        # ===== 股票市场 =====
        'stock': {'api': 'cn_stock', 'name': '股票市场', 'freq': '日度'},
        'index': {'api': 'cn_index', 'name': '指数', 'freq': '日度'},

        # ===== 债券 =====
        'bond': {'api': 'cn_bond', 'name': '债券市场', 'freq': '日度'},
    }

    def __init__(self, token=None):
        self.token = token or TUSHARE_TOKEN
        if not self.token:
            raise ValueError("未设置Tushare token")

        try:
            self.pro = ts.pro_api(self.token)
            self.pro._DataApi__token = self.token
            self.pro._DataApi__http_url = TUSHARE_HTTP_URL
            logger.info(f"成功初始化Tushare API")
        except Exception as e:
            logger.error(f"初始化Tushare API失败: {e}")
            raise

    def fetch_gdp(self, start_date='19900101'):
        """获取GDP数据"""
        try:
            logger.info("正在获取GDP数据...")
            df = self.pro.cn_gdp(start_date=start_date)

            if df.empty:
                return None

            # 处理季度数据
            result = []
            for _, row in df.iterrows():
                quarter = row['quarter']
                year, q = quarter.split('Q')
                date = pd.to_datetime(f'{year}-{int(q)*3:02d}-01')

                # GDP当前值
                result.append({
                    'date': date,
                    'value': row['gdp'],
                    'indicator_code': 'GDP',
                    'indicator_name': '国内生产总值',
                    'frequency': 'q'
                })

                # GDP同比
                if 'gdp_pyoy' in row and pd.notna(row['gdp_pyoy']):
                    result.append({
                        'date': date,
                        'value': row['gdp_pyoy'],
                        'indicator_code': 'GDP_YOY',
                        'indicator_name': 'GDP同比',
                        'frequency': 'q'
                    })

            return pd.DataFrame(result)

        except Exception as e:
            logger.error(f"获取GDP失败: {e}")
            return None

    def fetch_cpi(self, start_date='19900101'):
        """获取CPI数据"""
        try:
            logger.info("正在获取CPI数据...")
            df = self.pro.cn_cpi(start_date=start_date)

            if df.empty:
                return None

            result = []

            # CPI同比
            if 'nt_yoy' in df.columns:
                for _, row in df.iterrows():
                    date = pd.to_datetime(row['month'], format='%Y%m')
                    if pd.notna(row['nt_yoy']):
                        result.append({
                            'date': date,
                            'value': row['nt_yoy'],
                            'indicator_code': 'CPI_YOY',
                            'indicator_name': 'CPI同比',
                            'frequency': 'm'
                        })

            # 核心CPI
            if 'core_yoy' in df.columns:
                for _, row in df.iterrows():
                    date = pd.to_datetime(row['month'], format='%Y%m')
                    if pd.notna(row['core_yoy']):
                        result.append({
                            'date': date,
                            'value': row['core_yoy'],
                            'indicator_code': 'CORE_CPI_YOY',
                            'indicator_name': '核心CPI同比',
                            'frequency': 'm'
                        })

            return pd.DataFrame(result) if result else None

        except Exception as e:
            logger.error(f"获取CPI失败: {e}")
            return None

    def fetch_money_supply(self, start_date='19900101'):
        """获取货币供应量"""
        try:
            logger.info("正在获取货币供应量数据...")
            df = self.pro.cn_m(start_date=start_date)

            if df.empty:
                return None

            result = []

            # M2
            if 'm2' in df.columns:
                for _, row in df.iterrows():
                    date = pd.to_datetime(row['month'], format='%Y%m')
                    if pd.notna(row['m2']):
                        result.append({
                            'date': date,
                            'value': row['m2'],
                            'indicator_code': 'M2',
                            'indicator_name': 'M2货币供应量',
                            'frequency': 'm'
                        })

            # M1
            if 'm1' in df.columns:
                for _, row in df.iterrows():
                    date = pd.to_datetime(row['month'], format='%Y%m')
                    if pd.notna(row['m1']):
                        result.append({
                            'date': date,
                            'value': row['m1'],
                            'indicator_code': 'M1',
                            'indicator_name': 'M1货币供应量',
                            'frequency': 'm'
                        })

            # M0
            if 'm0' in df.columns:
                for _, row in df.iterrows():
                    date = pd.to_datetime(row['month'], format='%Y%m')
                    if pd.notna(row['m0']):
                        result.append({
                            'date': date,
                            'value': row['m0'],
                            'indicator_code': 'M0',
                            'indicator_name': 'M0货币供应量',
                            'frequency': 'm'
                        })

            return pd.DataFrame(result) if result else None

        except Exception as e:
            logger.error(f"获取货币供应量失败: {e}")
            return None

    def fetch_pmi(self, start_date='20050101'):
        """获取PMI数据"""
        try:
            logger.info("正在获取PMI数据...")
            df = self.pro.cn_pmi(start_date=start_date)

            if df.empty:
                return None

            result = []

            # 制造业PMI
            if 'PMI012000' in df.columns:
                for _, row in df.iterrows():
                    date = pd.to_datetime(row['MONTH'], format='%Y%m')
                    if pd.notna(row['PMI012000']):
                        result.append({
                            'date': date,
                            'value': row['PMI012000'],
                            'indicator_code': 'PMI',
                            'indicator_name': '制造业PMI',
                            'frequency': 'm'
                        })

            # 非制造业PMI
            if 'PMI022000' in df.columns:
                for _, row in df.iterrows():
                    date = pd.to_datetime(row['MONTH'], format='%Y%m')
                    if pd.notna(row['PMI022000']):
                        result.append({
                            'date': date,
                            'value': row['PMI022000'],
                            'indicator_code': 'NON_MFG_PMI',
                            'indicator_name': '非制造业PMI',
                            'frequency': 'm'
                        })

            return pd.DataFrame(result) if result else None

        except Exception as e:
            logger.error(f"获取PMI失败: {e}")
            return None

    def fetch_shibor(self, start_date='20060101', end_date=None):
        """获取Shibor数据"""
        try:
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')

            logger.info(f"正在获取Shibor数据 ({start_date} 至 {end_date})...")
            df = self.pro.shibor(start_date=start_date, end_date=end_date)

            if df.empty:
                return None

            result = []

            # 隔夜
            if 'on' in df.columns:
                for _, row in df.iterrows():
                    date = pd.to_datetime(row['date'], format='%Y%m%d')
                    if pd.notna(row['on']):
                        result.append({
                            'date': date,
                            'value': row['on'],
                            'indicator_code': 'SHIBOR_ON',
                            'indicator_name': 'Shibor隔夜',
                            'frequency': 'd'
                        })

            # 1周
            if '1w' in df.columns:
                for _, row in df.iterrows():
                    date = pd.to_datetime(row['date'], format='%Y%m%d')
                    if pd.notna(row['1w']):
                        result.append({
                            'date': date,
                            'value': row['1w'],
                            'indicator_code': 'SHIBOR_1W',
                            'indicator_name': 'Shibor1周',
                            'frequency': 'd'
                        })

            # 1个月
            if '1m' in df.columns:
                for _, row in df.iterrows():
                    date = pd.to_datetime(row['date'], format='%Y%m%d')
                    if pd.notna(row['1m']):
                        result.append({
                            'date': date,
                            'value': row['1m'],
                            'indicator_code': 'SHIBOR_1M',
                            'indicator_name': 'Shibor1月',
                            'frequency': 'd'
                        })

            return pd.DataFrame(result) if result else None

        except Exception as e:
            logger.error(f"获取Shibor失败: {e}")
            return None

    def fetch_industrial_production(self, start_date='19900101'):
        """获取工业增加值"""
        try:
            logger.info("正在获取工业增加值数据...")
            # 使用 cn_ind 接口
            df = self.pro.cn_ind(start_date=start_date)

            if df.empty:
                return None

            result = []
            for _, row in df.iterrows():
                date = pd.to_datetime(row['month'], format='%Y%m')
                if pd.notna(row['inc_va']):
                    result.append({
                        'date': date,
                        'value': row['inc_va'],
                        'indicator_code': 'IND_PROD_YOY',
                        'indicator_name': '工业增加值同比',
                        'frequency': 'm'
                    })

            return pd.DataFrame(result) if result else None

        except Exception as e:
            logger.error(f"获取工业增加值失败: {e}")
            return None

    def fetch_retail_sales(self, start_date='19900101'):
        """获取社会消费品零售总额"""
        try:
            logger.info("正在获取社会消费品零售总额数据...")
            df = self.pro.cn_retail(start_date=start_date)

            if df.empty:
                return None

            result = []
            for _, row in df.iterrows():
                date = pd.to_datetime(row['month'], format='%Y%m')
                if pd.notna(row['retail_yoy']):
                    result.append({
                        'date': date,
                        'value': row['retail_yoy'],
                        'indicator_code': 'RETAIL_YOY',
                        'indicator_name': '社零同比',
                        'frequency': 'm'
                    })

            return pd.DataFrame(result) if result else None

        except Exception as e:
            logger.error(f"获取社零失败: {e}")
            return None

    def fetch_fixed_asset_investment(self, start_date='20040101'):
        """获取固定资产投资"""
        try:
            logger.info("正在获取固定资产投资数据...")
            df = self.pro.cn_inv(start_date=start_date)

            if df.empty:
                return None

            result = []
            for _, row in df.iterrows():
                date = pd.to_datetime(row['month'], format='%Y%m')
                if pd.notna(row['inv_yoy']):
                    result.append({
                        'date': date,
                        'value': row['inv_yoy'],
                        'indicator_code': 'FAI_YOY',
                        'indicator_name': '固定资产投资同比',
                        'frequency': 'm'
                    })

            return pd.DataFrame(result) if result else None

        except Exception as e:
            logger.error(f"获取固定资产投资失败: {e}")
            return None

    def fetch_all_indicators(self, start_date='19900101'):
        """获取所有指标"""
        logger.info("="*80)
        logger.info(f"开始获取中国宏观数据，起始日期：{start_date}")
        logger.info("="*80)

        all_data = []

        # GDP
        df = self.fetch_gdp(start_date)
        if df is not None:
            all_data.append(df)
            logger.info(f"✓ GDP: {len(df)} 条")
            time.sleep(0.5)

        # CPI
        df = self.fetch_cpi(start_date)
        if df is not None:
            all_data.append(df)
            logger.info(f"✓ CPI: {len(df)} 条")
            time.sleep(0.5)

        # 货币供应量
        df = self.fetch_money_supply(start_date)
        if df is not None:
            all_data.append(df)
            logger.info(f"✓ 货币供应量: {len(df)} 条")
            time.sleep(0.5)

        # PMI
        df = self.fetch_pmi(start_date)
        if df is not None:
            all_data.append(df)
            logger.info(f"✓ PMI: {len(df)} 条")
            time.sleep(0.5)

        # Shibor（最近2年）
        shibor_start = (datetime.now() - pd.DateOffset(years=2)).strftime('%Y%m%d')
        df = self.fetch_shibor(start_date=shibor_start)
        if df is not None:
            all_data.append(df)
            logger.info(f"✓ Shibor: {len(df)} 条")
            time.sleep(0.5)

        # 工业增加值
        df = self.fetch_industrial_production(start_date)
        if df is not None:
            all_data.append(df)
            logger.info(f"✓ 工业增加值: {len(df)} 条")
            time.sleep(0.5)

        # 社零
        df = self.fetch_retail_sales(start_date)
        if df is not None:
            all_data.append(df)
            logger.info(f"✓ 社零: {len(df)} 条")
            time.sleep(0.5)

        # 固定资产投资
        df = self.fetch_fixed_asset_investment(start_date)
        if df is not None:
            all_data.append(df)
            logger.info(f"✓ 固定资产投资: {len(df)} 条")
            time.sleep(0.5)

        # 合并所有数据
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            result = result.sort_values('date').reset_index(drop=True)

            logger.info(f"\n{'='*80}")
            logger.info(f"成功获取 {len(result)} 条数据")
            logger.info(f"时间范围：{result['date'].min()} 至 {result['date'].max()}")
            logger.info(f"指标数量：{result['indicator_code'].nunique()}")
            logger.info(f"{'='*80}")

            # 保存
            output_path = project_root / 'data' / 'csv' / 'cn_all_indicators_extended.csv'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"\n数据已保存到：{output_path}")

            return result
        else:
            logger.error("没有获取到任何数据")
            return pd.DataFrame()


def main():
    """主函数"""
    try:
        fetcher = ExtendedCNDataFetcher()
        df = fetcher.fetch_all_indicators(start_date='19900101')

        if not df.empty:
            print("\n✅ 数据获取完成！")
            print("\n指标列表：")
            for code in sorted(df['indicator_code'].unique()):
                name = df[df['indicator_code']==code]['indicator_name'].iloc[0]
                count = len(df[df['indicator_code']==code])
                print(f"  - {code}: {name} ({count} 条)")
        else:
            print("\n❌ 数据获取失败")

    except Exception as e:
        logger.error(f"程序执行失败: {e}")


if __name__ == '__main__':
    main()
