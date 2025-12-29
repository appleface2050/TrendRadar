"""
获取美国宏观数据（简化版）
分批获取核心指标，避免超时
"""
import pandas as pd
import pandas_datareader.data as web
from datetime import datetime, timedelta
import time
import logging
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from configs.db_config import FRED_API_KEY

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置FRED API key
if FRED_API_KEY:
    os.environ['FRED_API_KEY'] = FRED_API_KEY
    logger.info(f"使用FRED API key")

# 核心指标（分批）
BATCH_1 = {
    # GDP
    'GDP': 'Gross Domestic Product',
    'GDPC1': 'Real GDP',

    # 通胀
    'CPIAUCSL': 'CPI All Items',
    'CPILFESL': 'Core CPI',
    'PCEPI': 'PCE Price Index',

    # 就业
    'UNRATE': 'Unemployment Rate',
    'PAYEMS': 'Nonfarm Payrolls',
}

BATCH_2 = {
    # PMI
    'NAPM': 'PMI Composite',

    # 工业产值
    'INDPRO': 'Industrial Production',
    'MCUMFN': 'Capacity Utilization',

    # 零售销售
    'RSXFS': 'Retail Sales',

    # 住房
    'HOUST': 'Housing Starts',
    'PERMIT': 'Building Permits',
}

BATCH_3 = {
    # 利率
    'FEDFUNDS': 'Federal Funds Rate',
    'DGS10': '10-Year Treasury',
    'DGS2': '2-Year Treasury',
    'DGS3MO': '3-Month Treasury',
    'T10Y2Y': '10Y-2Y Spread',
    'T10Y3M': '10Y-3M Spread',
}

BATCH_4 = {
    # 货币供应量
    'M1SL': 'M1 Money Supply',
    'M2SL': 'M2 Money Supply',
    'BOGMBASE': 'Monetary Base',

    # 消费者信心
    'UMCSENT': 'Consumer Sentiment',

    # 汇率
    'DEXUSEU': 'USD/EUR',
    'DTWEXBGS': 'Dollar Index',
}

BATCH_5 = {
    # 股票市场
    'SP500': 'S&P 500',

    # 财政
    'FYFSGDA188S': 'Federal Budget Balance',
    'GFDEBTN': 'Federal Debt',
}

ALL_BATCHES = [BATCH_1, BATCH_2, BATCH_3, BATCH_4, BATCH_5]


def fetch_batch(batch_dict, batch_name, start_date='1950-01-01'):
    """获取一批指标"""
    logger.info(f"\n{'='*60}")
    logger.info(f"获取 {batch_name} ({len(batch_dict)} 个指标)")
    logger.info(f"{'='*60}")

    all_data = []

    for i, (code, name) in enumerate(batch_dict.items(), 1):
        try:
            logger.info(f"[{i}/{len(batch_dict)}] {code}: {name}")

            df = web.DataReader(code, 'fred', start=start_date)

            if df.empty:
                logger.warning(f"  没有数据")
                continue

            # 转换为长格式
            df = df.reset_index()
            df.columns = ['date', 'value']
            df['indicator_code'] = code
            df['indicator_name'] = name

            logger.info(f"  ✓ {len(df)} 条数据 ({df['date'].min()} 至 {df['date'].max()})")

            all_data.append(df)
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"  ✗ 失败: {e}")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()


def main():
    """主函数"""
    logger.info("="*80)
    logger.info("开始获取美国宏观数据（分批）")
    logger.info("="*80)

    all_data = []
    batch_names = ['第1批：GDP和通胀', '第2批：PMI和工业', '第3批：利率',
                   '第4批：货币和汇率', '第5批：其他']

    for batch, name in zip(ALL_BATCHES, batch_names):
        df = fetch_batch(batch, name, start_date='1950-01-01')
        if not df.empty:
            all_data.append(df)
            time.sleep(1)

    # 合并所有数据
    if all_data:
        result = pd.concat(all_data, ignore_index=True)

        logger.info(f"\n{'='*80}")
        logger.info(f"成功获取 {len(result)} 条数据")
        logger.info(f"时间范围：{result['date'].min()} 至 {result['date'].max()}")
        logger.info(f"指标数量：{result['indicator_code'].nunique()}")
        logger.info(f"{'='*80}")

        # 保存
        output_path = project_root / 'data' / 'csv' / 'us_all_indicators_extended.csv'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"\n数据已保存到：{output_path}")

        print("\n✅ 数据获取完成！")
        print("\n指标列表：")
        for code in sorted(result['indicator_code'].unique()):
            name = result[result['indicator_code']==code]['indicator_name'].iloc[0]
            count = len(result[result['indicator_code']==code])
            print(f"  - {code}: {name} ({count} 条)")

        return result
    else:
        logger.error("没有获取到任何数据")
        return pd.DataFrame()


if __name__ == '__main__':
    df = main()
