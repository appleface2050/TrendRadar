"""
使用 AKShare 补充获取缺失的数据

AKShare 是免费的财经数据接口，无需注册
支持的数据：
1. M1/M2 货币供应量
2. 国债收益率
3. 部分宏观数据

安装：
pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple

运行方式：
python scripts/fetch_missing_data_akshare.py
"""

import sys
from pathlib import Path
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def fetch_m1_m2_akshare():
    """使用 AKShare 获取 M1/M2 数据"""
    print("="*80)
    print("使用 AKShare 获取 M1/M2 数据...")
    print("-"*80)

    try:
        import akshare as ak

        # 获取 M1 和 M2 数据
        print("  获取 M2 数据...")
        m2_df = ak.macro_china_m2_year()

        print("  获取 M1 数据...")
        m1_df = ak.macro_china_m1_year()

        # 合并数据
        m2_df = m2_df.sort_values('月份')
        m1_df = m1_df.sort_values('月份')

        # 重命名列
        m2_df.rename(columns={'月份': 'date', '货币和准货币(M2)': 'M2'}, inplace=True)
        m1_df.rename(columns={'月份': 'date', '货币(M1)': 'M1'}, inplace=True)

        # 合并
        df = pd.merge(m2_df[['date', 'M2']], m1_df[['date', 'M1']], on='date', how='outer')
        df = df.sort_values('date')

        # 转换日期格式
        df['date'] = pd.to_datetime(df['date'], format='%Y年%m月').dt.strftime('%Y-%m-%d')

        # 保存
        output_dir = Path('data/processed/china')
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / 'm1_m2.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"  ✅ 成功获取 {len(df)} 条记录")
        print(f"     时间范围: {df['date'].min()} 至 {df['date'].max()}")
        print(f"     已保存至: {output_file}")

        return True

    except ImportError:
        print("  ❌ AKShare 未安装")
        print("  💡 安装命令: pip install akshare")
        return False
    except Exception as e:
        print(f"  ❌ 获取失败: {str(e)}")
        return False


def fetch_bond_yield_akshare():
    """使用 AKShare 获取国债收益率"""
    print("\n"+"="*80)
    print("使用 AKShare 获取国债收益率...")
    print("-"*80)

    try:
        import akshare as ak

        # 获取中国10年期国债收益率
        print("  获取10年期国债收益率...")

        # 使用中债网数据
        df = ak.bond_china_yield(start_date="20160101", end_date="20241231")

        if df.empty:
            print("  ⚠️ AKShare 返回空数据")
            return False

        # 处理数据
        df = df.sort_values('date')

        # 选择10年期国债收益率
        if '10年' in df.columns:
            df = df[['date', '10年']]
            df.rename(columns={'10年': 'yield'}, inplace=True)
        elif '10Y' in df.columns:
            df = df[['date', '10Y']]
            df.rename(columns={'10Y': 'yield'}, inplace=True)
        else:
            print(f"  ⚠️ 可用的列: {df.columns.tolist()}")
            print(df.head())
            return False

        # 保存
        output_dir = Path('data/processed/china')
        output_file = output_dir / 'bond_yield_10y.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"  ✅ 成功获取 {len(df)} 条记录")
        print(f"     时间范围: {df['date'].min()} 至 {df['date'].max()}")
        print(f"     已保存至: {output_file}")

        return True

    except ImportError:
        print("  ❌ AKShare 未安装")
        print("  💡 安装命令: pip install akshare")
        return False
    except Exception as e:
        print(f"  ❌ 获取失败: {str(e)}")
        return False


def fetch_vix_akshare():
    """使用 AKShare 获取 VIX 数据"""
    print("\n"+"="*80)
    print("使用 AKShare 获取 VIX 数据...")
    print("-"*80)

    try:
        import akshare as ak

        # 获取 VIX 指数
        print("  获取 VIX 指数...")
        df = ak.index_us_stock_sina(symbol=".VIX")

        if df.empty:
            print("  ⚠️ AKShare 返回空数据")
            return False

        # 处理数据
        df = df.sort_values('date')
        df.rename(columns={'close': 'vix'}, inplace=True)
        df = df[['date', 'vix']]

        # 保存
        output_dir = Path('data/processed/global')
        output_file = output_dir / 'vix.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"  ✅ 成功获取 {len(df)} 条记录")
        print(f"     时间范围: {df['date'].min()} 至 {df['date'].max()}")
        print(f"     已保存至: {output_file}")

        return True

    except Exception as e:
        print(f"  ❌ 获取失败: {str(e)}")
        return False


def fetch_sp500_akshare():
    """使用 AKShare 获取 SP500 数据"""
    print("\n"+"="*80)
    print("使用 AKShare 获取 SP500 数据...")
    print("-"*80)

    try:
        import akshare as ak

        # 获取 SP500 指数
        print("  获取 SP500 指数...")
        df = ak.index_us_stock_sina(symbol=".INX")

        if df.empty:
            print("  ⚠️ AKShare 返回空数据")
            return False

        # 处理数据
        df = df.sort_values('date')

        # 保存
        output_dir = Path('data/processed/us')
        output_file = output_dir / 'sp500.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"  ✅ 成功获取 {len(df)} 条记录")
        print(f"     时间范围: {df['date'].min()} 至 {df['date'].max()}")
        print(f"     已保存至: {output_file}")

        return True

    except Exception as e:
        print(f"  ❌ 获取失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("🚀 使用 AKShare 补充获取缺失的数据...")
    print()

    results = {}

    # 获取各类数据
    results['m1_m2'] = fetch_m1_m2_akshare()
    results['bond_yield'] = fetch_bond_yield_akshare()
    results['vix'] = fetch_vix_akshare()
    results['sp500'] = fetch_sp500_akshare()

    # 生成摘要
    print("\n"+"="*80)
    print("数据获取摘要")
    print("="*80)

    success = [k for k, v in results.items() if v is True]
    failed = [k for k, v in results.items() if v is False]

    if success:
        print(f"\n✅ 成功获取 {len(success)} 项:")
        for item in success:
            print(f"   - {item}")

    if failed:
        print(f"\n❌ 获取失败 {len(failed)} 项:")
        for item in failed:
            print(f"   - {item}")

    print("\n下一步:")
    print("1. 检查生成的数据文件")
    print("2. 运行第三阶段模型计算宏观数据")
    print("3. 运行回测")
    print("="*80)


if __name__ == "__main__":
    main()
