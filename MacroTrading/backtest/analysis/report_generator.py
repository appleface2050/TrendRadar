"""
回测报告生成器

生成详细的回测报告

功能：
1. 整合绩效指标
2. 生成HTML报告
3. 生成PDF报告（可选）
4. 导出CSV数据
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')


class ReportGenerator:
    """
    回测报告生成器
    """

    def __init__(self):
        """初始化"""
        self.report_data = None

    def generate_report(
        self,
        backtest_results: Dict,
        attribution_results: Optional[Dict] = None,
        output_format: str = 'html'
    ) -> str:
        """
        生成回测报告

        Parameters:
        -----------
        backtest_results : dict
            回测结果
        attribution_results : dict, optional
            归因分析结果
        output_format : str
            输出格式：'html', 'text', 'markdown'

        Returns:
        --------
        str
            报告内容
        """
        self.report_data = {
            'backtest': backtest_results,
            'attribution': attribution_results,
            'generated_at': datetime.now()
        }

        if output_format == 'html':
            return self._generate_html_report()
        elif output_format == 'markdown':
            return self._generate_markdown_report()
        else:
            return self._generate_text_report()

    def _generate_html_report(self) -> str:
        """生成HTML报告"""
        html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>宏观策略回测报告</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        h2 {
            color: #666;
            margin-top: 30px;
            border-left: 4px solid #4CAF50;
            padding-left: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .metric {
            display: inline-block;
            margin: 10px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
            min-width: 200px;
        }
        .metric-label {
            color: #666;
            font-size: 14px;
        }
        .metric-value {
            color: #333;
            font-size: 24px;
            font-weight: bold;
            margin-top: 5px;
        }
        .positive {
            color: #4CAF50;
        }
        .negative {
            color: #f44336;
        }
        .timestamp {
            color: #999;
            font-size: 12px;
            text-align: right;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>宏观策略回测报告</h1>
        <p class="timestamp">生成时间: {timestamp}</p>
"""

        # 添加回测结果
        if self.report_data['backtest']:
            html += self._add_backtest_section_html()

        # 添加归因分析结果
        if self.report_data['attribution']:
            html += self._add_attribution_section_html()

        html += """
    </div>
</body>
</html>
"""

        return html.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def _add_backtest_section_html(self) -> str:
        """添加回测结果HTML部分"""
        backtest = self.report_data['backtest']
        metrics = backtest.get('metrics', {})
        benchmark = backtest.get('benchmark', {}).get('metrics', {})

        html = """
        <h2>一、回测绩效概览</h2>

        <div class="metrics">
            <div class="metric">
                <div class="metric-label">策略总收益</div>
                <div class="metric-value {pos_class}">{total_return}</div>
            </div>
            <div class="metric">
                <div class="metric-label">年化收益</div>
                <div class="metric-value {pos_class}">{annual_return}</div>
            </div>
            <div class="metric">
                <div class="metric-label">夏普比率</div>
                <div class="metric-value">{sharpe}</div>
            </div>
            <div class="metric">
                <div class="metric-label">最大回撤</div>
                <div class="metric-value {neg_class}">{max_dd}</div>
            </div>
        </div>

        <h2>二、策略 vs 基准对比</h2>
        <table>
            <tr>
                <th>指标</th>
                <th>宏观策略</th>
                <th>买入持有</th>
                <th>超额</th>
            </tr>
            <tr>
                <td>总收益率</td>
                <td>{str_total}</td>
                <td>{bn_total}</td>
                <td>{excess}</td>
            </tr>
            <tr>
                <td>年化收益率</td>
                <td>{str_ann}</td>
                <td>{bn_ann}</td>
                <td>{excess_ann}</td>
            </tr>
            <tr>
                <td>夏普比率</td>
                <td>{str_sharpe}</td>
                <td>{bn_sharpe}</td>
                <td>{excess_sharpe}</td>
            </tr>
            <tr>
                <td>最大回撤</td>
                <td>{str_dd}</td>
                <td>{bn_dd}</td>
                <td>{excess_dd}</td>
            </tr>
        </table>
"""

        # 填充数据
        total_return = metrics.get('total_return', 0)
        annual_return = metrics.get('annual_return', 0)
        sharpe = metrics.get('sharpe_ratio', 0)
        max_dd = metrics.get('max_drawdown', 0)

        bn_total = benchmark.get('total_return', 0)
        bn_ann = benchmark.get('annual_return', 0)
        bn_sharpe = benchmark.get('sharpe_ratio', 0)
        bn_dd = benchmark.get('max_drawdown', 0)

        html = html.format(
            pos_class='positive' if total_return >= 0 else 'negative',
            neg_class='negative' if max_dd < 0 else 'positive',
            total_return=f"{total_return:.2%}",
            annual_return=f"{annual_return:.2%}",
            sharpe=f"{sharpe:.2f}",
            max_dd=f"{max_dd:.2%}",
            str_total=f"{total_return:.2%}",
            bn_total=f"{bn_total:.2%}",
            excess=f"{(total_return - bn_total):.2%}",
            str_ann=f"{annual_return:.2%}",
            bn_ann=f"{bn_ann:.2%}",
            excess_ann=f"{(annual_return - bn_ann):.2%}",
            str_sharpe=f"{sharpe:.2f}",
            bn_sharpe=f"{bn_sharpe:.2f}",
            excess_sharpe=f"{(sharpe - bn_sharpe):.2f}",
            str_dd=f"{max_dd:.2%}",
            bn_dd=f"{bn_dd:.2%}",
            excess_dd=f"{(max_dd - bn_dd):.2%}"
        )

        return html

    def _add_attribution_section_html(self) -> str:
        """添加归因分析HTML部分"""
        attribution = self.report_data['attribution']

        html = """
        <h2>三、绩效归因分析</h2>
        <table>
            <tr>
                <th>归因项</th>
                <th>数值</th>
            </tr>
            <tr>
                <td>资产配置效应</td>
                <td>{alloc_effect}</td>
            </tr>
            <tr>
                <td>择时效应</td>
                <td>{timing_effect}</td>
            </tr>
            <tr>
                <td>风险调整收益</td>
                <td>{risk_adj}</td>
            </tr>
        </table>
"""

        # 简化处理
        risk_adj = attribution.get('risk_adjusted_return', {})

        html = html.format(
            alloc_effect="详见分析报告",
            timing_effect=f"相关系数: {attribution.get('timing_effect', {}).get('correlation', 0):.2f}",
            risk_adj=f"夏普: {risk_adj.get('sharpe_ratio', 0):.2f}, 卡玛: {risk_adj.get('calmar_ratio', 0):.2f}"
        )

        return html

    def _generate_markdown_report(self) -> str:
        """生成Markdown报告"""
        md = f"""# 宏观策略回测报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 一、回测绩效概览

"""

        # 添加回测结果
        if self.report_data['backtest']:
            md += self._add_backtest_section_md()

        # 添加归因分析
        if self.report_data['attribution']:
            md += self._add_attribution_section_md()

        return md

    def _add_backtest_section_md(self) -> str:
        """添加回测结果Markdown部分"""
        backtest = self.report_data['backtest']
        metrics = backtest.get('metrics', {})
        benchmark = backtest.get('benchmark', {}).get('metrics', {})

        total_return = metrics.get('total_return', 0)
        annual_return = metrics.get('annual_return', 0)
        sharpe = metrics.get('sharpe_ratio', 0)
        max_dd = metrics.get('max_drawdown', 0)

        bn_total = benchmark.get('total_return', 0)

        md = f"""### 关键指标

- **策略总收益**: {total_return:.2%}
- **年化收益**: {annual_return:.2%}
- **夏普比率**: {sharpe:.2f}
- **最大回撤**: {max_dd:.2%}
- **最终资产**: {metrics.get('final_equity', 0):.2f}

### 策略 vs 基准

| 指标 | 宏观策略 | 买入持有 | 超额 |
|------|---------|---------|------|
| 总收益率 | {total_return:.2%} | {bn_total:.2%} | {(total_return - bn_total):.2%} |
| 年化收益率 | {annual_return:.2%} | {benchmark.get('annual_return', 0):.2%} | {(annual_return - benchmark.get('annual_return', 0)):.2%} |
| 夏普比率 | {sharpe:.2f} | {benchmark.get('sharpe_ratio', 0):.2f} | {(sharpe - benchmark.get('sharpe_ratio', 0)):.2f} |
| 最大回撤 | {max_dd:.2%} | {benchmark.get('max_drawdown', 0):.2%} | {(max_dd - benchmark.get('max_drawdown', 0)):.2%} |

"""

        return md

    def _add_attribution_section_md(self) -> str:
        """添加归因分析Markdown部分"""
        attribution = self.report_data['attribution']

        md = """## 二、绩效归因分析

### 收益分解

- **策略总收益**: {:.2%}
- **基准收益**: {:.2%}
- **超额收益**: {:.2%}

### 风险调整收益

- **年化波动**: {:.2%}
- **夏普比率**: {:.2f}
- **索提诺比率**: {:.2f}
- **卡玛比率**: {:.2f}

""".format(
            attribution.get('total_return', 0),
            attribution.get('benchmark_return', 0),
            attribution.get('excess_return', 0),
            attribution.get('risk_adjusted_return', {}).get('annual_volatility', 0),
            attribution.get('risk_adjusted_return', {}).get('sharpe_ratio', 0),
            attribution.get('risk_adjusted_return', {}).get('sortino_ratio', 0),
            attribution.get('risk_adjusted_return', {}).get('calmar_ratio', 0)
        )

        return md

    def _generate_text_report(self) -> str:
        """生成文本报告"""
        text = self._generate_markdown_report()
        return text

    def save_report(
        self,
        content: str,
        output_file: str,
        output_format: str = 'html'
    ):
        """
        保存报告到文件

        Parameters:
        -----------
        content : str
            报告内容
        output_file : str
            输出文件路径
        output_format : str
            输出格式
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"报告已保存到: {output_file}")
