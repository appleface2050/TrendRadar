"""
指标重要性分析演示

演示如何使用 analyze_indicator_importance 方法分析DFM模型中各指标的重要性
"""

import sys
sys.path.insert(0, '.')

from MacroTrading.models.dfm.us_dfm import USDFM


def main():
    print("="*80)
    print("美国DFM模型 - 指标重要性分析演示")
    print("="*80)

    # 1. 创建模型
    print("\n[步骤1] 创建美国DFM模型...")
    us_dfm = USDFM(
        n_factors=3,
        factor_orders=2,
        standardize=True
    )
    print("✓ 模型初始化完成")

    # 2. 加载数据
    print("\n[步骤2] 加载美国宏观数据...")
    data = us_dfm.fetch_from_csv(
        csv_path='data/processed/us/us_all_indicators.csv',
        start_date='2014-01-01'
    )
    print(f"✓ 数据加载成功：{len(data)}个时间点，{len(data.columns)}个指标")
    print(f"  时间范围：{data.index.min()} 至 {data.index.max()}")

    # 3. 拟合模型
    print("\n[步骤3] 拟合DFM模型...")
    us_dfm.fit(data, method='pca')
    print(f"✓ 模型拟合完成")
    print(f"  PCA解释方差比：{us_dfm.pca_model.explained_variance_ratio_}")
    print(f"  累计解释方差比：{us_dfm.pca_model.explained_variance_ratio_.cumsum()}")

    # 4. 分析指标重要性
    print("\n[步骤4] 分析指标重要性...")
    importance = us_dfm.analyze_indicator_importance(
        high_threshold=0.7,
        medium_threshold=0.4
    )

    # 5. 详细展示结果
    print("\n" + "="*80)
    print("各因子的指标贡献详情")
    print("="*80)

    for factor_name, factor_data in importance['by_factor'].items():
        print(f"\n【{factor_name}】")

        high = factor_data['high_contribution']['indicators']
        medium = factor_data['medium_contribution']['indicators']
        low = factor_data['low_contribution']['indicators']

        if high:
            print(f"  高贡献（≥0.7）：{high}")
            for ind in high[:3]:  # 显示前3个的载荷值
                print(f"    - {ind}: {factor_data['high_contribution']['loadings'][ind]:.4f}")

        if medium:
            print(f"  中贡献（0.4-0.7）：{medium}")

        print(f"  低贡献（<0.4）：{len(low)}个指标")

    # 6. 整体重要性排名
    print("\n" + "="*80)
    print("整体指标重要性排名（Top 10）")
    print("="*80)

    for indicator, info in sorted(
        importance['overall_importance'].items(),
        key=lambda x: x[1]['rank']
    )[:10]:
        print(f"\n{info['rank']:2d}. {indicator}")
        print(f"     最大载荷: {info['max_loading']:.4f} ({info['max_loading_factor']})")
        print(f"     平均载荷: {info['mean_loading']:.4f}")

    # 7. 生成可视化
    print("\n[步骤5] 生成可视化...")
    try:
        for i in range(us_dfm.n_factors):
            fig = us_dfm.plot_indicator_importance(
                factor_index=i,
                top_n=15,
                figsize=(12, 8)
            )
            output_path = f'MacroTrading/models/dfm/indicator_importance_factor_{i+1}.png'
            fig.savefig(output_path, dpi=100, bbox_inches='tight')
            print(f"  ✓ 图表已保存：{output_path}")
    except Exception as e:
        print(f"  ✗ 绘图失败：{e}")

    # 8. 分析建议
    print("\n" + "="*80)
    print("📊 分析建议")
    print("="*80)

    key_indicators = importance['key_indicators']
    redundant_indicators = importance['redundant_indicators']

    print(f"\n✓ 关键指标（{len(key_indicators)}个）：")
    print(f"  这些指标对因子解释贡献最大，应优先保证数据质量")
    if key_indicators:
        # 将数字代码转换为更有意义的名称（如果可能）
        print(f"  指标代码：{key_indicators}")

    if redundant_indicators:
        print(f"\n⚠ 冗余指标（{len(redundant_indicators)}个）：")
        print(f"  这些指标载荷较低，可以考虑：")
        print(f"  1. 删除以简化模型")
        print(f"  2. 替换为更相关的指标")
        print(f"  指标代码：{redundant_indicators}")
    else:
        print(f"\n✓ 没有明显的冗余指标，当前指标配置合理")

    # 9. 保存详细结果
    print("\n[步骤6] 保存分析结果...")
    import json

    output_json = 'MacroTrading/models/dfm/indicator_importance_analysis.json'
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(importance, f, indent=2, ensure_ascii=False)

    print(f"✓ 详细分析结果已保存：{output_json}")

    print("\n" + "="*80)
    print("✅ 分析完成！")
    print("="*80)

    return importance


if __name__ == '__main__':
    result = main()
