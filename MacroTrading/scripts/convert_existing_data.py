"""
转换现有数据为回测所需格式

项目中已有大量历史数据，本脚本将其转换为回测所需的格式

运行方式：
python scripts/convert_existing_data.py
"""

import sys
from pathlib import Path
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_processor import DataProcessor
from utils.data_validator import DataValidator
from utils.data_logger import DataLogger


def convert_money_supply():
    """转换货币供应量数据"""
    print("=" * 80)
    print("转换中国 M1/M2 数据...")
    print("-" * 80)

    # 初始化工具
    processor = DataProcessor(logger=DataLogger())
    validator = None

    try:
        # 读取原始数据
        input_file = Path(__file__).parent.parent.parent / 'data/processed/china/cn_money_supply.csv'

        if not input_file.exists():
            processor.logger.log_warning("文件检查", f"文件不存在: {input_file}")
            return False

        df = processor.read_csv(input_file)
        processor.logger.log_success("读取数据", f"成功读取 {len(df)} 条记录")

        # 验证输入数据
        validator = DataValidator(df, 'cn_money_supply')
        if not validator.validate_required_columns(['date', 'indicator_code', 'value']):
            processor.logger.log_error("验证", ValueError("缺少必需列"))
            return False

        # 处理数据
        df = processor.standardize_date(df, 'date')
        df = processor.filter_by_date(df, 'date', start_date='2016-01-01')

        # 长格式转宽格式
        df_pivot = processor.pivot_to_wide(df, 'date', 'indicator_code', 'value')

        # 选择M1和M2列
        if 'M1' in df_pivot.columns and 'M2' in df_pivot.columns:
            result = df_pivot[['date', 'M1', 'M2']].copy()
        else:
            processor.logger.log_warning(
                "列检查",
                f"可用的指标: {df_pivot.columns.tolist()}"
            )
            return False

        # 保存
        output_file = Path('data/processed/china/m1_m2.csv')
        processor.save_csv(result, output_file)

        # 生成质量报告
        quality_report = processor.validate_and_report(result, 'm1_m2')
        processor.logger.log_success(
            "convert_money_supply",
            f"成功转换 {len(result)} 条记录，时间范围: {result['date'].min()} 至 {result['date'].max()}"
        )

        return True

    except Exception as e:
        processor.logger.log_error("convert_money_supply", e)
        return False


def convert_bond_yield():
    """转换国债收益率数据"""
    print("\n" + "=" * 80)
    print("转换中国国债收益率数据...")
    print("-" * 80)

    # 初始化工具
    processor = DataProcessor(logger=DataLogger())

    try:
        # 读取原始数据
        input_file = Path(__file__).parent.parent.parent / 'data/processed/china/cn_shibor.csv'

        if not input_file.exists():
            processor.logger.log_warning("文件检查", f"未找到 SHIBOR 数据: {input_file}")
            return False

        df = processor.read_csv(input_file)

        # 筛选2016年及以后的数据
        df = processor.standardize_date(df, 'date')
        df = processor.filter_by_date(df, 'date', start_date='2016-01-01')

        # 查找长期限的利率数据
        # 如果有1年期SHIBOR，可以作为代理
        if '1Y' in df.columns:
            result = df[['date', '1Y']].copy()
            result.rename(columns={'1Y': 'yield'}, inplace=True)
        elif '6M' in df.columns:
            result = df[['date', '6M']].copy()
            result.rename(columns={'6M': 'yield'}, inplace=True)
        else:
            processor.logger.log_warning(
                "列检查",
                f"可用的列: {df.columns.tolist()}"
            )
            return False

        # 保存
        output_file = Path('data/processed/china/bond_yield_10y.csv')
        processor.save_csv(result, output_file)

        # 生成质量报告
        quality_report = processor.validate_and_report(result, 'bond_yield')
        processor.logger.log_success(
            "convert_bond_yield",
            f"成功转换 {len(result)} 条记录（使用SHIBOR作为代理），"
            f"时间范围: {result['date'].min()} 至 {result['date'].max()}"
        )
        processor.logger.log_info("💡 注意: 使用SHIBOR利率代替国债收益率")

        return True

    except Exception as e:
        processor.logger.log_error("convert_bond_yield", e)
        return False


def convert_vix():
    """转换VIX数据"""
    print("\n" + "=" * 80)
    print("转换 VIX 数据...")
    print("-" * 80)

    # 初始化工具
    processor = DataProcessor(logger=DataLogger())

    try:
        # 读取原始数据
        input_file = Path(__file__).parent.parent.parent / 'data/processed/global/vix.csv'

        if not input_file.exists():
            processor.logger.log_warning("文件检查", f"未找到 VIX 数据文件: {input_file}")
            return False

        # 尝试读取多种格式
        try:
            df = processor.read_csv(input_file, skiprows=2)
        except:
            df = processor.read_csv(input_file)

        # 标准化列名
        df = processor.clean_column_names(df, strip=True, lower=False)

        # 重命名列
        if 'Date' in df.columns:
            df.rename(columns={'Date': 'date'}, inplace=True)

        if 'vix' not in df.columns:
            if 'close' in df.columns:
                df.rename(columns={'close': 'vix'}, inplace=True)
            elif 'Close' in df.columns:
                df.rename(columns={'Close': 'vix'}, inplace=True)
            else:
                processor.logger.log_error("列检查", ValueError("未找到 VIX 数据列"))
                return False

        # 选择需要的列
        if 'date' in df.columns and 'vix' in df.columns:
            df = df[['date', 'vix']].copy()
            df = df.dropna(subset=['vix'])
        else:
            processor.logger.log_error(
                "数据验证",
                ValueError(f"未识别的数据格式，可用的列: {df.columns.tolist()}")
            )
            return False

        # 转换日期格式
        df = processor.standardize_date(df, 'date')
        df = processor.filter_by_date(df, 'date', start_date='2016-01-01')

        # 保存
        output_file = Path('data/processed/global/vix.csv')
        processor.save_csv(df, output_file)

        # 生成质量报告
        quality_report = processor.validate_and_report(df, 'vix')
        processor.logger.log_success(
            "convert_vix",
            f"成功转换 {len(df)} 条记录，时间范围: {df['date'].min()} 至 {df['date'].max()}"
        )

        return True

    except Exception as e:
        processor.logger.log_error("convert_vix", e)
        return False


def check_us_bond_yield():
    """检查美国国债收益率数据"""
    print("\n" + "=" * 80)
    print("检查美国国债收益率数据...")
    print("-" * 80)

    processor = DataProcessor(logger=DataLogger())

    project_root = Path(__file__).parent.parent.parent
    output_file = project_root / 'data/processed/global/us_bond_yield_10y.csv'

    if output_file.exists():
        try:
            # 尝试读取，跳过注释行
            df = processor.read_csv(output_file, comment='#')

            # 检查是否有实际数据
            if df.shape[0] > 0:
                processor.logger.log_success(
                    "数据检查",
                    f"已有数据: {len(df)} 条记录"
                )
                return True
        except:
            pass

    processor.logger.log_warning("数据检查", "需要手动获取美国10年期国债收益率")
    processor.logger.log_info("💡 建议方式:")
    processor.logger.log_info("   1. FRED API: https://fred.stlouisfed.org/series/GS10")
    processor.logger.log_info("   2. yfinance: import yfinance as yf; tbill = yf.download('^TNX', ...)")
    processor.logger.log_info(f"   3. 手动下载后保存到: {output_file}")

    return False


def main():
    """主函数"""
    print("🚀 转换现有数据为回测所需格式...")
    print()

    results = {}

    # 转换各类数据
    results['m1_m2'] = convert_money_supply()
    results['bond_yield'] = convert_bond_yield()
    results['vix'] = convert_vix()
    results['us_bond_yield'] = check_us_bond_yield()

    # 生成摘要
    print("\n" + "=" * 80)
    print("数据转换摘要")
    print("=" * 80)

    success = [k for k, v in results.items() if v is True]
    failed = [k for k, v in results.items() if v is False]

    if success:
        print(f"\n✅ 成功转换 {len(success)} 项:")
        for item in success:
            print(f"   - {item}")

    if failed:
        print(f"\n⚠️  需要手动处理 {len(failed)} 项:")
        for item in failed:
            print(f"   - {item}")

    print("\n" + "=" * 80)
    print("检查生成的数据文件:")
    print("  data/processed/china/m1_m2.csv")
    print("  data/processed/china/bond_yield_10y.csv")
    print("  data/processed/global/vix.csv")
    print("=" * 80)


if __name__ == "__main__":
    main()
