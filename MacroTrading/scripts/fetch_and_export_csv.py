"""
数据获取和导出脚本
从 FRED 和 Tushare 获取宏观数据并导出为 CSV
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data_handlers.us.us_data_fetcher import USDataFetcher
from data_handlers.cn.tushare_fetcher import CNDataFetcher
from utils.data_processor import DataProcessor
from utils.data_validator import DataValidator
from utils.data_logger import DataLogger

# 创建 CSV 输出目录
CSV_OUTPUT_DIR = project_root / 'data' / 'csv'
CSV_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_indicator_data(processor, data, filename, indicator_name, validate=True):
    """
    保存指标数据到 CSV

    Args:
        processor: DataProcessor 实例
        data: 要保存的数据框
        filename: 输出文件名
        indicator_name: 指标名称（用于日志）
        validate: 是否验证数据质量

    Returns:
        bool: 是否成功保存
    """
    try:
        if data.empty:
            processor.logger.log_warning(
                indicator_name,
                f"数据为空，跳过保存"
            )
            return False

        # 验证数据
        if validate:
            report = processor.validate_and_report(data, indicator_name)
            if report['total_rows'] == 0:
                processor.logger.log_warning(
                    indicator_name,
                    "没有有效数据"
                )
                return False

        # 保存 CSV
        output_file = CSV_OUTPUT_DIR / filename
        success = processor.save_csv(data, output_file)

        if success:
            processor.logger.log_success(
                indicator_name,
                f"数据已保存: {output_file.name} ({len(data):,} 条记录)"
            )
        else:
            processor.logger.log_error(
                indicator_name,
                Exception(f"保存文件失败: {output_file}")
            )

        return success

    except Exception as e:
        processor.logger.log_error(indicator_name, e)
        return False


def fetch_us_data():
    """获取美国宏观数据并导出为 CSV"""
    processor = DataProcessor(logger=DataLogger())

    processor.logger.log_info("=" * 60)
    processor.logger.log_info("开始获取美国宏观数据（FRED）")
    processor.logger.log_info("=" * 60)

    try:
        fetcher = USDataFetcher()
        start_date = '2014-01-01'

        # 定义要获取的指标
        indicators = [
            ('GDP', 'GDP', 'us_gdp.csv'),
            ('CPIAUCSL', 'CPI', 'us_cpi.csv'),
            ('UNRATE', '失业率', 'us_unrate.csv'),
            ('FEDFUNDS', '联邦基金利率', 'us_fedfunds.csv'),
            ('GS10', '10年期国债收益率', 'us_gs10.csv'),
            ('INDPRO', '工业产值', 'us_indpro.csv'),
            ('RSXFS', '零售销售', 'us_retail.csv'),
        ]

        # 获取各个指标
        for code, name, filename in indicators:
            processor.logger.log_info(f"\n获取 {name} 数据...")

            try:
                data = fetcher.fetch_indicator(code, start=start_date)
                save_indicator_data(processor, data, filename, f"US-{name}")

            except Exception as e:
                processor.logger.log_error(
                    f"US-{name}",
                    e
                )

        # 获取所有核心指标
        processor.logger.log_info("\n获取所有核心指标...")
        try:
            all_data = fetcher.fetch_all_core_indicators(start=start_date)
            save_indicator_data(
                processor,
                all_data,
                'us_all_indicators.csv',
                'US-所有指标'
            )
        except Exception as e:
            processor.logger.log_error("US-所有指标", e)

        processor.logger.log_info("\n" + "=" * 60)
        processor.logger.log_success("美国数据获取", "完成！")
        processor.logger.log_info("=" * 60)

        return True

    except Exception as e:
        processor.logger.log_error("获取美国数据", e)
        return False


def fetch_cn_data():
    """获取中国宏观数据并导出为 CSV"""
    processor = DataProcessor(logger=DataLogger())

    processor.logger.log_info("\n" + "=" * 60)
    processor.logger.log_info("开始获取中国宏观数据（Tushare）")
    processor.logger.log_info("=" * 60)

    try:
        fetcher = CNDataFetcher()

        if not fetcher.pro:
            processor.logger.log_error(
                "Tushare API",
                Exception("未初始化，请检查配置")
            )
            return False

        start_date = '20140101'

        # GDP
        processor.logger.log_info("\n获取 GDP 数据...")
        try:
            gdp_data = fetcher.fetch_gdp(start_date=start_date)
            save_indicator_data(processor, gdp_data, 'cn_gdp.csv', 'CN-GDP')
        except Exception as e:
            processor.logger.log_error("CN-GDP", e)

        # CPI
        processor.logger.log_info("\n获取 CPI 数据...")
        try:
            cpi_data = fetcher.fetch_cpi(start_date=start_date)
            save_indicator_data(processor, cpi_data, 'cn_cpi.csv', 'CN-CPI')
        except Exception as e:
            processor.logger.log_error("CN-CPI", e)

        # PPI
        processor.logger.log_info("\n获取 PPI 数据...")
        try:
            ppi_data = fetcher.fetch_ppi(start_date=start_date)
            save_indicator_data(processor, ppi_data, 'cn_ppi.csv', 'CN-PPI')
        except Exception as e:
            processor.logger.log_error("CN-PPI", e)

        # 货币供应量
        processor.logger.log_info("\n获取货币供应量数据...")
        try:
            money_data = fetcher.fetch_money_supply(start_date=start_date)
            save_indicator_data(
                processor,
                money_data,
                'cn_money_supply.csv',
                'CN-货币供应量'
            )
        except Exception as e:
            processor.logger.log_error("CN-货币供应量", e)

        # PMI
        processor.logger.log_info("\n获取 PMI 数据...")
        try:
            pmi_data = fetcher.fetch_pmi(start_date=start_date)
            save_indicator_data(processor, pmi_data, 'cn_pmi.csv', 'CN-PMI')
        except Exception as e:
            processor.logger.log_error("CN-PMI", e)

        # Shibor（最近1年）
        processor.logger.log_info("\n获取 Shibor 数据...")
        try:
            shibor_start = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            shibor_data = fetcher.fetch_shibor(start_date=shibor_start)
            save_indicator_data(processor, shibor_data, 'cn_shibor.csv', 'CN-Shibor')
        except Exception as e:
            processor.logger.log_error("CN-Shibor", e)

        # 获取所有核心指标
        processor.logger.log_info("\n获取所有核心指标...")
        try:
            all_data = fetcher.fetch_all_core_indicators(start_date=start_date)
            save_indicator_data(
                processor,
                all_data,
                'cn_all_indicators.csv',
                'CN-所有指标'
            )
        except Exception as e:
            processor.logger.log_error("CN-所有指标", e)

        processor.logger.log_info("\n" + "=" * 60)
        processor.logger.log_success("中国数据获取", "完成！")
        processor.logger.log_info("=" * 60)

        return True

    except Exception as e:
        processor.logger.log_error("获取中国数据", e)
        return False


def main():
    """主函数"""
    logger = DataLogger()

    logger.log_info("\n" + "=" * 60)
    logger.log_info("数据获取和导出脚本")
    logger.log_info("=" * 60)
    logger.log_info(f"CSV 输出目录: {CSV_OUTPUT_DIR}")
    logger.log_info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 获取美国数据
    us_success = fetch_us_data()

    # 获取中国数据
    cn_success = fetch_cn_data()

    # 总结
    logger.log_info("\n" + "=" * 60)
    logger.log_info("任务完成总结")
    logger.log_info("=" * 60)
    logger.log_info(
        f"美国数据: {'✓ 成功' if us_success else '✗ 失败'}"
    )
    logger.log_info(
        f"中国数据: {'✓ 成功' if cn_success else '✗ 失败'}"
    )
    logger.log_info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.log_info("=" * 60)

    if us_success or cn_success:
        logger.log_info(f"\nCSV 文件已保存到: {CSV_OUTPUT_DIR}")

        # 列出所有生成的文件
        csv_files = list(CSV_OUTPUT_DIR.glob('*.csv'))
        if csv_files:
            logger.log_info("\n生成的文件:")
            for f in sorted(csv_files):
                file_size = f.stat().st_size
                logger.log_info(f"  - {f.name} ({file_size:,} bytes)")


if __name__ == "__main__":
    main()
