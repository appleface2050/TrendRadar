"""
获取美国10年期国债收益率

使用 FRED API 获取美国10年期国债收益率数据

运行方式：
python scripts/fetch_us_bond_yield.py
"""

import sys
from pathlib import Path
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def fetch_us_treasury_10y_fred():
    """使用 FRED API 获取美国10年期国债收益率"""
    print("="*80)
    print("使用 FRED API 获取美国10年期国债收益率...")
    print("-"*80)

    try:
        # 尝试使用 pandas_datareader
        try:
            import pandas_datareader as pdr
            from datetime import datetime

            start = datetime(2016, 1, 1)
            end = datetime(2024, 12, 31)

            print("  正在下载美国10年期国债收益率...")
            print(f"  时间范围: {start.strftime('%Y-%m-%d')} 至 {end.strftime('%Y-%m-%d')}")

            # 获取数据（FRED系列代码：GS10）
            df = pdr.DataReader('GS10', 'fred', start=start, end=end)

            if df.empty:
                print("  ⚠️ FRED 返回空数据")
                return False

            # 重置索引并重命名列
            df = df.reset_index()
            df.rename(columns={'DATE': 'date', 'GS10': 'yield'}, inplace=True)
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')

            # 保存
            output_dir = Path('data/processed/global')
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / 'us_bond_yield_10y.csv'

            df.to_csv(output_file, index=False, encoding='utf-8-sig')

            print(f"  ✅ 成功获取 {len(df)} 条记录")
            print(f"     时间范围: {df['date'].min()} 至 {df['date'].max()}")
            print(f"     已保存至: {output_file}")

            return True

        except ImportError:
            print("  ❌ pandas_datareader 未安装")
            print("  💡 安装命令:")
            print("     pip install pandas_datareader")
            return False

    except Exception as e:
        print(f"  ❌ 获取失败: {str(e)}")
        return False


def fetch_us_treasury_10y_yfinance():
    """使用 yfinance 获取美国10年期国债收益率"""
    print("\n"+"="*80)
    print("使用 yfinance 获取美国10年期国债收益率...")
    print("-"*80)

    try:
        import yfinance as yf

        print("  正在下载...")
        # 使用 ^TNX (10年期国债收益率期货) 或 ^IRX (13周国债)
        df = yf.download('^TNX', start='2016-01-01', end='2024-12-31', progress=False)

        if df.empty:
            print("  ⚠️ yfinance 返回空数据")
            return False

        # 重置索引并重命名列
        df = df.reset_index()
        df.rename(columns={'Date': 'date', 'Close': 'yield'}, inplace=True)
        df = df[['date', 'yield']].copy()
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')

        # 保存
        output_dir = Path('data/processed/global')
        output_file = output_dir / 'us_bond_yield_10y.csv'

        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"  ✅ 成功获取 {len(df)} 条记录")
        print(f"     时间范围: {df['date'].min()} 至 {df['date'].max()}")
        print(f"     已保存至: {output_file}")

        return True

    except ImportError:
        print("  ❌ yfinance 未安装")
        print("  💡 安装命令:")
        print("     pip install yfinance")
        return False
    except Exception as e:
        print(f"  ❌ 获取失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("🚀 获取美国10年期国债收益率...")
    print()

    # 尝试多种数据源
    print("尝试方案1: FRED API（推荐）")
    result1 = fetch_us_treasury_10y_fred()

    if not result1:
        print("\n尝试方案2: yfinance（备用）")
        result2 = fetch_us_treasury_10y_yfinance()

        if not result2:
            print("\n"+"="*80)
            print("⚠️ 自动获取失败，请手动下载")
            print("="*80)
            print("方式1: FRED 网站")
            print("  网址: https://fred.stlouisfed.org/series/GS10")
            print("  下载: 点击 'Download Data' → 'Download Data (CSV)'")
            print("  保存到: data/processed/global/us_bond_yield_10y.csv")
            print()
            print("方式2: 使用 pandas_datareader")
            print("  ```python")
            print("  import pandas_datareader as pdr")
            print("  from datetime import datetime")
            print("  start = datetime(2016, 1, 1)")
            print("  end = datetime(2024, 12, 31)")
            print("  df = pdr.DataReader('GS10', 'fred', start=start, end=end)")
            print("  df.to_csv('data/processed/global/us_bond_yield_10y.csv')")
            print("  ```")
            print("="*80)
            return

    print("\n✅ 数据获取成功！")
    print("下一步: 运行回测")
    print("  python scripts/run_backtest.py")


if __name__ == "__main__":
    main()
