"""
测试指标重要性分析功能

演示如何使用 analyze_indicator_importance 方法
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from MacroTrading.models.dfm.us_dfm import USDFM


def test_indicator_importance_analysis():
    """测试指标重要性分析"""
    print("="*80)
    print("测试指标重要性分析功能")
    print("="*80)

    # 创建美国DFM模型
    us_dfm = USDFM(
        n_factors=3,
        factor_orders=2,
        standardize=True
    )

    # 加载数据
    print("\n[1] 加载数据...")
    try:
        data = us_dfm.fetch_from_csv(
            csv_path='../../data/processed/us/us_all_indicators.csv',
            start_date='2014-01-01'
        )
        print(f"✓ 数据加载成功：{len(data)}个时间点，{len(data.columns)}个指标")
    except FileNotFoundError:
        print("✗ 数据文件未找到，请确保 data/processed/us/us_all_indicators.csv 存在")
        return None

    # 拟合模型
    print("\n[2] 拟合DFM模型...")
    us_dfm.fit(data, method='pca')
    print(f"✓ 模型拟合完成")

    # 分析指标重要性
    print("\n[3] 分析指标重要性...")
    importance = us_dfm.analyze_indicator_importance(
        high_threshold=0.7,
        medium_threshold=0.4
    )

    # 详细输出每个因子的指标分类
    print("\n" + "="*80)
    print("各因子的指标贡献详情")
    print("="*80)

    for factor_name, factor_data in importance['by_factor'].items():
        print(f"\n【{factor_name}】")
        print(f"  高贡献指标（≥0.7）：{factor_data['high_contribution']['indicators']}")
        print(f"  中贡献指标（0.4-0.7）：{factor_data['medium_contribution']['indicators']}")
        print(f"  低贡献指标（<0.4）：{len(factor_data['low_contribution']['indicators'])}个")

    # 输出整体重要性排名（Top 10）
    print("\n" + "="*80)
    print("整体指标重要性排名（Top 10）")
    print("="*80)

    rank = 1
    for indicator, info in sorted(
        importance['overall_importance'].items(),
        key=lambda x: x[1]['rank']
    ):
        if rank > 10:
            break
        print(f"\n{rank}. {indicator}")
        print(f"   最大载荷: {info['max_loading']:.4f} ({info['max_loading_factor']})")
        print(f"   平均载荷: {info['mean_loading']:.4f}")
        rank += 1

    # 绘制指标重要性图
    print("\n[4] 生成可视化...")
    try:
        for i in range(us_dfm.n_factors):
            fig = us_dfm.plot_indicator_importance(
                factor_index=i,
                top_n=15,
                figsize=(12, 8)
            )

            # 保存图表
            output_path = f'MacroTrading/tests/indicator_importance_factor_{i+1}.png'
            fig.savefig(output_path, dpi=100, bbox_inches='tight')
            print(f"  ✓ 图表已保存：{output_path}")

    except Exception as e:
        print(f"  ✗ 绘图失败：{e}")

    # 分析建议
    print("\n" + "="*80)
    print("分析建议")
    print("="*80)

    key_indicators = importance['key_indicators']
    redundant_indicators = importance['redundant_indicators']

    print(f"\n✓ 关键指标（{len(key_indicators)}个）：")
    print(f"  这些指标对因子解释贡献最大，应优先保证数据质量")
    print(f"  {key_indicators}")

    if redundant_indicators:
        print(f"\n⚠ 冗余指标（{len(redundant_indicators)}个）：")
        print(f"  这些指标载荷较低，可考虑：")
        print(f"  1. 删除以简化模型")
        print(f"  2. 替换为更相关的指标")
        print(f"  {redundant_indicators}")
    else:
        print(f"\n✓ 没有明显的冗余指标，当前指标配置合理")

    # 保存详细分析结果
    print("\n[5] 保存详细分析结果...")
    import json

    output_json = 'MacroTrading/tests/indicator_importance_analysis.json'
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(importance, f, indent=2, ensure_ascii=False)

    print(f"✓ 分析结果已保存：{output_json}")

    print("\n" + "="*80)
    print("测试完成！")
    print("="*80)

    return importance


if __name__ == '__main__':
    result = test_indicator_importance_analysis()
