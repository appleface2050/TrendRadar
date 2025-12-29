"""
转换现有数据为回测所需格式

项目中已有大量历史数据，本脚本将其转换为回测所需的格式

运行方式：
python scripts/convert_existing_data.py
"""

import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


def convert_money_supply():
    """转换货币供应量数据"""
    print("="*80)
    print("转换中国 M1/M2 数据...")
    print("-"*80)

    try:
        # 读取原始数据（使用项目根目录的绝对路径）
        project_root = Path(__file__).parent.parent.parent
        input_file = project_root / 'data/processed/china/cn_money_supply.csv'
        df = pd.read_csv(input_file)

        # 筛选2016年及以后的数据
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['date'] >= '2016-01-01']

        # 转换为宽格式
        df_pivot = df.pivot(index='date', columns='indicator_code', values='value')

        # 重置索引
        df_pivot = df_pivot.reset_index()
        df_pivot['date'] = df_pivot['date'].dt.strftime('%Y-%m-%d')

        # 选择M1和M2列
        if 'M1' in df_pivot.columns and 'M2' in df_pivot.columns:
            result = df_pivot[['date', 'M1', 'M2']].copy()
        else:
            print(f"  ⚠️ 可用的指标: {df_pivot.columns.tolist()}")
            return False

        # 保存
        output_file = Path('data/processed/china/m1_m2.csv')
        result.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"  ✅ 成功转换 {len(result)} 条记录")
        print(f"     时间范围: {result['date'].min()} 至 {result['date'].max()}")
        print(f"     已保存至: {output_file}")

        return True

    except Exception as e:
        print(f"  ❌ 转换失败: {str(e)}")
        return False


def convert_bond_yield():
    """转换国债收益率数据"""
    print("\n"+"="*80)
    print("转换中国国债收益率数据...")
    print("-"*80)

    try:
        # 使用项目根目录的绝对路径
        project_root = Path(__file__).parent.parent.parent
        input_file = project_root / 'data/processed/china/cn_shibor.csv'

        if not input_file.exists():
            print("  ⚠️ 未找到 SHIBOR 数据")
            return False

        df = pd.read_csv(input_file)

        # 筛选2016年及以后的数据
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['date'] >= '2016-01-01']

        # 查找长期限的利率数据
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')

        # 如果有1年期SHIBOR，可以作为代理
        if '1Y' in df.columns:
            result = df[['date', '1Y']].copy()
            result.rename(columns={'1Y': 'yield'}, inplace=True)
        elif '6M' in df.columns:
            result = df[['date', '6M']].copy()
            result.rename(columns={'6M': 'yield'}, inplace=True)
        else:
            print(f"  ⚠️ 可用的列: {df.columns.tolist()}")
            return False

        # 保存
        output_file = Path('data/processed/china/bond_yield_10y.csv')
        result.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"  ✅ 成功转换 {len(result)} 条记录 (使用SHIBOR作为代理)")
        print(f"     时间范围: {result['date'].min()} 至 {result['date'].max()}")
        print(f"     已保存至: {output_file}")
        print("  💡 注意: 使用SHIBOR利率代替国债收益率")

        return True

    except Exception as e:
        print(f"  ❌ 转换失败: {str(e)}")
        return False


def convert_vix():
    """转换VIX数据"""
    print("\n"+"="*80)
    print("转换 VIX 数据...")
    print("-"*80)

    try:
        # 使用项目根目录的绝对路径
        project_root = Path(__file__).parent.parent.parent
        input_file = project_root / 'data/processed/global/vix.csv'

        if not input_file.exists():
            print("  ⚠️ 未找到 VIX 数据文件")
            return False

        # 尝试读取多种格式
        try:
            df = pd.read_csv(input_file, skiprows=2)
        except:
            df = pd.read_csv(input_file)

        # 筛选2016年及以后的数据
        if 'Date' in df.columns:
            df.rename(columns={'Date': 'date', 'Close': 'vix'}, inplace=True)
            df = df[['date', 'vix']].copy()
            df = df.dropna()

        elif 'date' in df.columns:
            if 'close' in df.columns:
                df.rename(columns={'close': 'vix'}, inplace=True)
            elif 'Close' in df.columns:
                df.rename(columns={'Close': 'vix'}, inplace=True)

            df = df[['date', 'vix']].copy()
            df = df.dropna()
        else:
            print(f"  ⚠️ 未识别的数据格式")
            print(f"     可用的列: {df.columns.tolist()}")
            return False

        # 转换日期格式
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['date'] >= '2016-01-01']
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')

        # 保存
        output_file = Path('data/processed/global/vix.csv')
        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"  ✅ 成功转换 {len(df)} 条记录")
        print(f"     时间范围: {df['date'].min()} 至 {df['date'].max()}")
        print(f"     已保存至: {output_file}")

        return True

    except Exception as e:
        print(f"  ❌ 转换失败: {str(e)}")
        return False


def check_us_bond_yield():
    """检查美国国债收益率数据"""
    print("\n"+"="*80)
    print("检查美国国债收益率数据...")
    print("-"*80)

    project_root = Path(__file__).parent.parent.parent
    output_file = project_root / 'data/processed/global/us_bond_yield_10y.csv'

    if output_file.exists():
        try:
            # 尝试读取，跳过注释行
            df = pd.read_csv(output_file, comment='#')

            # 检查是否有实际数据
            if df.shape[0] > 0:
                print(f"  ✅ 已有数据: {len(df)} 条记录")
                return True
        except:
            pass

    print("  ⚠️ 需要手动获取美国10年期国债收益率")
    print("  💡 建议方式:")
    print("     1. FRED API: https://fred.stlouisfed.org/series/GS10")
    print("     2. yfinance: import yfinance as yf; tbill = yf.download('^TNX', ...)")
    print(f"     3. 手动下载后保存到: {output_file}")

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
    print("\n"+"="*80)
    print("数据转换摘要")
    print("="*80)

    success = [k for k, v in results.items() if v is True]
    failed = [k for k, v in results.items() if v is False]

    if success:
        print(f"\n✅ 成功转换 {len(success)} 项:")
        for item in success:
            print(f"   - {item}")

    if failed:
        print(f"\n⚠️ 需要手动处理 {len(failed)} 项:")
        for item in failed:
            print(f"   - {item}")

    print("\n"+"="*80)
    print("检查生成的数据文件:")
    print("  data/processed/china/m1_m2.csv")
    print("  data/processed/china/bond_yield_10y.csv")
    print("  data/processed/global/vix.csv")
    print("="*80)


if __name__ == "__main__":
    main()
