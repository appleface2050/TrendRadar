"""
一键获取回测所需的所有数据

功能：
1. 中国数据：价格、M1/M2、债券收益率、北向资金流、行业指数
2. 美国数据：SP500、国债收益率、VIX、美元指数
3. 自动保存到指定目录
4. 进度显示和错误处理

运行方式：
python scripts/fetch_all_backtest_data.py
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from configs.db_config import TUSHARE_TOKEN, TUSHARE_HTTP_URL


class BacktestDataFetcher:
    """回测数据获取器"""

    def __init__(self):
        """初始化"""
        self.token = TUSHARE_TOKEN
        if not self.token:
            raise ValueError("未找到Tushare Token，请配置 confidential.json")

        # 尝试导入tushare
        try:
            import tushare as ts

            # 参考 tushare_example.py 的正确方式
            # 先创建实例（不传 token）
            self.pro = ts.pro_api()

            # 然后直接设置私有属性
            self.pro._DataApi__token = self.token
            print(f"✅ Tushare Token 已配置: {self.token}")

            # 如果配置了自定义 endpoint，同样直接设置
            if TUSHARE_HTTP_URL:
                self.pro._DataApi__http_url = TUSHARE_HTTP_URL
                print(f"✅ 使用自定义 endpoint: {TUSHARE_HTTP_URL}")

        except Exception as e:
            raise ImportError(f"无法导入 tushare: {str(e)}")

        # 创建输出目录
        self.output_dirs = {
            'china_prices': Path('data/processed/china'),
            'china_macro': Path('data/processed/china'),
            'us_prices': Path('data/processed/us'),
            'us_macro': Path('data/processed/global'),
            'industries': Path('data/processed/china/industries'),
            'derived': Path('data/derived/indicators')
        }

        for dir_path in self.output_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

        self.fetch_results = {}

    def fetch_china_index(self, start_date='20160101', end_date='20241231'):
        """获取中国沪深300指数数据"""
        print("\n" + "="*80)
        print("1/10 获取中国沪深300指数数据...")
        print("-"*80)

        try:
            # 获取沪深300指数
            df = self.pro.index_daily(
                ts_code='000300.SH',  # 沪深300
                start_date=start_date,
                end_date=end_date
            )

            if df.empty:
                print("  ❌ 未获取到数据")
                return False

            # 处理数据
            df = df.sort_values('trade_date')
            df.rename(columns={
                'trade_date': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'vol': 'volume'
            }, inplace=True)

            # 选择需要的列
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

            # 保存
            output_file = self.output_dirs['china_prices'] / 'hs300.csv'
            df.to_csv(output_file, index=False, encoding='utf-8-sig')

            print(f"  ✅ 成功获取 {len(df)} 条记录")
            print(f"     时间范围: {df['date'].min()} 至 {df['date'].max()}")
            print(f"     已保存至: {output_file}")

            self.fetch_results['hs300'] = True
            return True

        except Exception as e:
            print(f"  ❌ 获取失败: {str(e)}")
            self.fetch_results['hs300'] = False
            return False

    def fetch_china_m1_m2(self, start_date='20160101', end_date='20241231'):
        """获取中国M1/M2数据"""
        print("\n"+"="*80)
        print("2/10 获取中国M1/M2数据...")
        print("-"*80)

        try:
            # 使用 sh_mz 接口获取货币供应量数据
            print("  获取货币供应量数据...")
            df = self.pro.sh_mz(
                start_date=start_date,
                end_date=end_date
            )

            if df.empty:
                print("  ❌ 未获取到数据")
                return False

            # 处理数据
            df = df.sort_values('trade_date')
            df.rename(columns={'trade_date': 'date'}, inplace=True)

            # 选择需要的列（M1, M2）
            # 根据实际返回的列名调整
            if 'm2' in df.columns and 'm1' in df.columns:
                df = df[['date', 'm1', 'm2']]
                df.rename(columns={'m1': 'M1', 'm2': 'M2'}, inplace=True)
            else:
                print(f"  ⚠️ 可用的列: {df.columns.tolist()}")
                # 打印前几行供调试
                print(df.head())
                return False

            # 保存
            output_file = self.output_dirs['china_macro'] / 'm1_m2.csv'
            df.to_csv(output_file, index=False, encoding='utf-8-sig')

            print(f"  ✅ 成功获取 {len(df)} 条记录")
            print(f"     时间范围: {df['date'].min()} 至 {df['date'].max()}")
            print(f"     已保存至: {output_file}")

            self.fetch_results['m1_m2'] = True
            return True

        except Exception as e:
            print(f"  ❌ 获取失败: {str(e)}")
            # 尝试备选方案
            print("  💡 尝试使用 cn接口 方式...")
            try:
                # 尝试使用其他接口
                df = self.pro.cn(method='m2', start_date=start_date.replace('-', ''), end_date=end_date.replace('-', ''))
                print(f"  备选接口返回列: {df.columns.tolist()}")
                print(df.head())
            except Exception as e2:
                print(f"  备选方案也失败: {str(e2)}")

            self.fetch_results['m1_m2'] = False
            return False

    def fetch_china_bond_yield(self, start_date='20160101', end_date='20241231'):
        """获取中国10年期国债收益率"""
        print("\n"+"="*80)
        print("3/10 获取中国10年期国债收益率...")
        print("-"*80)

        try:
            # 使用 shibor 接口获取国债收益率
            # 或者使用 zk 接口获取中债数据
            print("  尝试获取中债国债收益率...")

            # 方案1: 使用 cn_bnd 接口
            df = self.pro.cn_bnd(
                ts_code='020005.IB',  # 10年期国债
                start_date=start_date,
                end_date=end_date
            )

            if df.empty:
                print("  ⚠️ cn_bnd 接口无数据，尝试其他方案...")

                # 方案2: 直接使用公开数据源
                print("  💡 建议使用以下方式获取:")
                print("     1. 中国债券信息网 (中债登): http://www.chinabond.com.cn/")
                print("     2. 中国货币网: https://www.chinamoney.com.cn/")
                print("     3. Wind/Choice 终端导出")

                # 创建占位文件
                output_file = self.output_dirs['china_macro'] / 'bond_yield_10y.csv'
                with open(output_file, 'w', encoding='utf-8-sig') as f:
                    f.write("date,yield\n")
                    f.write("# 请从中国债券信息网下载10年期国债收益率数据\n")
                    f.write("# 网址: http://www.chinabond.com.cn/\n")

                print(f"  📝 已创建示例文件: {output_file}")
                self.fetch_results['bond_yield'] = 'manual'
                return True

            # 处理数据
            df = df.sort_values('trade_date')
            df.rename(columns={'trade_date': 'date'}, inplace=True)

            # 提取收益率列（根据实际返回列调整）
            if 'yield' in df.columns:
                df = df[['date', 'yield']]
            else:
                print(f"  ⚠️ 可用的列: {df.columns.tolist()}")
                print(df.head())
                return False

            # 保存
            output_file = self.output_dirs['china_macro'] / 'bond_yield_10y.csv'
            df.to_csv(output_file, index=False, encoding='utf-8-sig')

            print(f"  ✅ 成功获取 {len(df)} 条记录")
            print(f"     时间范围: {df['date'].min()} 至 {df['date'].max()}")
            print(f"     已保存至: {output_file}")

            self.fetch_results['bond_yield'] = True
            return True

        except Exception as e:
            print(f"  ❌ 获取失败: {str(e)}")
            print("  💡 该数据需要从中国债券信息网手动下载")
            self.fetch_results['bond_yield'] = False
            return False

    def fetch_northbound_flow(self, start_date='20170317', end_date='20241231'):
        """获取北向资金流数据"""
        print("\n"+"="*80)
        print("4/10 获取北向资金流数据...")
        print("-"*80)

        try:
            # 获取沪深港通资金流向
            df = self.pro.moneyflow_hsgt(
                start_date=start_date,
                end_date=end_date
            )

            if df.empty:
                print("  ❌ 未获取到数据")
                return False

            # 处理数据
            df = df.sort_values('trade_date')

            # 计算净流入（沪股通+深股通）
            df['northbound_flow'] = df['ggt_ss'] + df['north_money']  # 沪股通 + 深股通

            # 选择需要的列
            df = df[['trade_date', 'northbound_flow']]
            df.rename(columns={'trade_date': 'date'}, inplace=True)

            # 保存
            output_file = self.output_dirs['china_macro'] / 'northbound_flow.csv'
            df.to_csv(output_file, index=False, encoding='utf-8-sig')

            print(f"  ✅ 成功获取 {len(df)} 条记录")
            print(f"     时间范围: {df['date'].min()} 至 {df['date'].max()}")
            print(f"     已保存至: {output_file}")

            self.fetch_results['northbound_flow'] = True
            return True

        except Exception as e:
            print(f"  ❌ 获取失败: {str(e)}")
            self.fetch_results['northbound_flow'] = False
            return False

    def fetch_industry_indices(self, start_date='20160101', end_date='20241231'):
        """获取行业指数数据"""
        print("\n"+"="*80)
        print("5/10 获取行业指数数据...")
        print("-"*80)

        # 行业指数代码（中证行业指数）
        industries = {
            '金融': '000001.SH',  # 中证金融
            '科技': '000009.SH',  # 中证信息技术
            '消费': '000003.SH',  # 中证主要消费
            '工业': '000004.SH',  # 中证工业
            '能源': '000005.SH',  # 中证能源
            '材料': '000006.SH',  # 中证原材料
            '医药': '000007.SH',  # 中证医药卫生
            '公用': '000008.SH'   # 中证公用事业
        }

        success_count = 0

        for industry_name, ts_code in industries.items():
            try:
                print(f"  获取 {industry_name} 指数...")
                df = self.pro.index_daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )

                if not df.empty:
                    # 处理数据
                    df = df.sort_values('trade_date')
                    df.rename(columns={'trade_date': 'date'}, inplace=True)
                    df = df[['date', 'close']]

                    # 保存
                    output_file = self.output_dirs['industries'] / f'{industry_name}.csv'
                    df.to_csv(output_file, index=False, encoding='utf-8-sig')

                    print(f"    ✅ {len(df)} 条记录")
                    success_count += 1
                else:
                    print(f"    ❌ 无数据")

            except Exception as e:
                print(f"    ❌ 失败: {str(e)}")

        print(f"\n  ✅ 成功获取 {success_count}/{len(industries)} 个行业指数")
        self.fetch_results['industries'] = success_count > 0
        return success_count > 0

    def fetch_us_sp500(self, start_date='20160101', end_date='20241231'):
        """获取美国SP500指数"""
        print("\n"+"="*80)
        print("6/10 获取美国SP500指数...")
        print("-"*80)

        try:
            # Tushare 暂不支持美股，使用其他方法
            # 这里保存为占位符，实际可以使用 yfinance 或 FRED
            print("  ⚠️ Tushare 不支持美股数据")
            print("  💡 建议:")
            print("     - 使用 yfinance: pip install yfinance")
            print("     - 使用 FRED 数据源")
            print("     - 手动下载 SP500 数据")

            # 创建示例文件
            output_file = self.output_dirs['us_prices'] / 'sp500.csv'

            # 写入说明
            with open(output_file, 'w', encoding='utf-8-sig') as f:
                f.write("date,open,high,low,close,volume\n")
                f.write("# 请使用 yfinance 或 FRED 获取 SP500 数据\n")
                f.write("# 安装: pip install yfinance\n")
                f.write("# 代码示例:\n")
                f.write("# import yfinance as yf\n")
                f.write("# sp500 = yf.download('^GSPC', start='2016-01-01', end='2024-12-31')\n")
                f.write("# sp500.to_csv('sp500.csv')\n")

            print(f"  📝 已创建示例文件: {output_file}")

            self.fetch_results['sp500'] = 'manual'
            return True

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.fetch_results['sp500'] = False
            return False

    def fetch_us_treasury_10y(self):
        """获取美国10年期国债收益率（使用备用方案）"""
        print("\n"+"="*80)
        print("7/10 获取美国10年期国债收益率...")
        print("-"*80)

        try:
            print("  ⚠️ Tushare 不支持美国国债数据")
            print("  💡 建议使用 FRED 数据源")
            print("  📝 已创建示例文件，包含获取说明")

            output_file = self.output_dirs['us_macro'] / 'us_bond_yield_10y.csv'

            with open(output_file, 'w', encoding='utf-8-sig') as f:
                f.write("date,yield\n")
                f.write("# 请使用 FRED 或 yfinance 获取美国10年期国债收益率\n")
                f.write("# FRED: https://fred.stlouisfed.org/series/GS10\n")
                f.write("# 代码示例:\n")
                f.write("# import pandas_datareader as pdr\n")
                f.write("# start = datetime(2016, 1, 1)\n")
                f.write("# us_yield = pdr.DataReader('GS10', 'fred', start=start)\n")

            print(f"  📝 已创建示例文件: {output_file}")

            self.fetch_results['us_bond_yield'] = 'manual'
            return True

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.fetch_results['us_bond_yield'] = False
            return False

    def fetch_vix(self):
        """获取VIX波动率指数（备用方案）"""
        print("\n"+"="*80)
        print("8/10 获取VIX波动率指数...")
        print("-"*80)

        try:
            print("  ⚠️ Tushare 不支持VIX数据")
            print("  💡 建议使用 FRED 或 yfinance")
            print("  📝 已创建示例文件")

            output_file = self.output_dirs['us_macro'] / 'vix.csv'

            with open(output_file, 'w', encoding='utf-8-sig') as f:
                f.write("date,vix\n")
                f.write("# 请使用 FRED 或 yfinance 获取VIX数据\n")
                f.write("# FRED: https://fred.stlouisfed.org/series/VIXCLS\n")

            print(f"  📝 已创建示例文件: {output_file}")

            self.fetch_results['vix'] = 'manual'
            return True

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.fetch_results['vix'] = False
            return False

    def fetch_dxy(self):
        """获取美元指数（备用方案）"""
        print("\n"+"="*80)
        print("9/10 获取美元指数...")
        print("-"*80)

        try:
            print("  ⚠️ Tushare 不支持美元指数")
            print("  💡 建议使用 FRED 或 yfinance")
            print("  📝 已创建示例文件")

            output_file = self.output_dirs['us_macro'] / 'dxy.csv'

            with open(output_file, 'w', encoding='utf-8-sig') as f:
                f.write("date,dxy\n")
                f.write("# 请使用 FRED 或 yfinance 获取美元指数\n")
                f.write("# FRED: https://fred.stlouisfed.org/series/DTWEXBGS\n")

            print(f"  📝 已创建示例文件: {output_file}")

            self.fetch_results['dxy'] = 'manual'
            return True

        except Exception as e:
            print(f"  ❌ 失败: {str(e)}")
            self.fetch_results['dxy'] = False
            return False

    def fetch_us_data_alternative(self):
        """使用备用方案获取美国数据"""
        print("\n"+"="*80)
        print("10/10 尝试使用备用方案获取美国数据...")
        print("-"*80)

        try:
            # 尝试使用 pandas_datareader 或 yfinance
            print("  💡 检测 yfinance 可用性...")

            try:
                import yfinance as yf

                # SP500
                print("  下载 SP500 数据...")
                sp500 = yf.download('^GSPC', start='2016-01-01', end='2024-12-31', progress=False)
                sp500.to_csv(self.output_dirs['us_prices'] / 'sp500.csv', encoding='utf-8-sig')
                print(f"  ✅ SP500: {len(sp500)} 条记录")

                # VIX
                print("  下载 VIX 数据...")
                vix = yf.download('^VIX', start='2016-01-01', end='2024-12-31', progress=False)
                vix.to_csv(self.output_dirs['us_macro'] / 'vix.csv', encoding='utf-8-sig')
                print(f"  ✅ VIX: {len(vix)} 条记录")

                print("\n  ✅ 使用 yfinance 成功获取美国数据！")
                self.fetch_results['us_data_yf'] = True
                return True

            except ImportError:
                print("  ⚠️ yfinance 未安装")
                print("  💡 安装命令: pip install yfinance")
                self.fetch_results['us_data_yf'] = False
                return False

        except Exception as e:
            print(f"  ❌ 备用方案失败: {str(e)}")
            self.fetch_results['us_data_yf'] = False
            return False

    def generate_summary(self):
        """生成数据获取摘要报告"""
        print("\n"+"="*80)
        print("数据获取摘要报告")
        print("="*80)
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 统计成功/失败
        success_items = []
        failed_items = []
        manual_items = []

        for key, value in self.fetch_results.items():
            if value is True:
                success_items.append(key)
            elif value == 'manual':
                manual_items.append(key)
            else:
                failed_items.append(key)

        print(f"✅ 成功获取: {len(success_items)} 项")
        for item in success_items:
            print(f"   - {item}")

        if manual_items:
            print(f"\n📝 需要手动获取: {len(manual_items)} 项")
            print("   （已在文件中添加获取说明）")
            for item in manual_items:
                print(f"   - {item}")

        if failed_items:
            print(f"\n❌ 获取失败: {len(failed_items)} 项")
            for item in failed_items:
                print(f"   - {item}")

        print()
        print("="*80)
        print("数据文件保存位置:")
        print(f"  中国价格数据: {self.output_dirs['china_prices']}")
        print(f"  中国宏观数据: {self.output_dirs['china_macro']}")
        print(f"  行业数据: {self.output_dirs['industries']}")
        print(f"  美国价格数据: {self.output_dirs['us_prices']}")
        print(f"  美国宏观数据: {self.output_dirs['us_macro']}")
        print("="*80)

        # 下一步建议
        print("\n下一步:")
        print("1. 检查获取的数据文件")
        print("2. 如有缺失，根据文件中的说明手动获取")
        print("3. 运行第三阶段模型计算宏观数据:")
        print("   python scripts/train_models_with_extended_data.py")
        print("4. 运行回测:")
        print("   python scripts/run_backtest.py")
        print("="*80)

    def fetch_all(self):
        """获取所有数据"""
        print("🚀 开始获取回测所需的所有数据...")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 获取中国数据
        self.fetch_china_index()
        self.fetch_china_m1_m2()
        self.fetch_china_bond_yield()
        self.fetch_northbound_flow()
        self.fetch_industry_indices()

        # 获取美国数据
        self.fetch_us_sp500()
        self.fetch_us_treasury_10y()
        self.fetch_vix()
        self.fetch_dxy()

        # 备用方案
        self.fetch_us_data_alternative()

        # 生成摘要
        self.generate_summary()

        print(f"\n✨ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """主函数"""
    print("="*80)
    print("回测数据自动获取工具")
    print("="*80)

    try:
        fetcher = BacktestDataFetcher()
        fetcher.fetch_all()

    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        print("请检查:")
        print("1. Tushare Token 是否正确配置")
        print("2. 网络连接是否正常")
        print("3. Tushare API 配额是否充足")


if __name__ == "__main__":
    main()
