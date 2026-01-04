# 指标重要性分析功能使用指南

## 功能概述

为 `BaseDFM` 类添加了 `analyze_indicator_importance()` 方法，用于分析DFM模型中各指标对因子提取的贡献程度。

### 核心价值

1. **识别关键指标**：找出对因子解释贡献最大的指标（载荷≥0.7）
2. **发现冗余指标**：识别载荷很低的指标（载荷<0.4），可考虑删除
3. **优化数据获取**：优先保证高贡献指标的数据质量
4. **模型简化**：删除冗余指标，降低数据获取成本

---

## 使用方法

### 基础用法

```python
from MacroTrading.models.dfm.us_dfm import USDFM

# 创建模型
us_dfm = USDFM(n_factors=3)

# 加载数据
data = us_dfm.fetch_from_csv('data/processed/us/us_all_indicators.csv')

# 拟合模型
us_dfm.fit(data, method='pca')

# 分析指标重要性
importance = us_dfm.analyze_indicator_importance()
```

### 自定义阈值

```python
importance = us_dfm.analyze_indicator_importance(
    high_threshold=0.7,     # 高贡献阈值（默认0.7）
    medium_threshold=0.4,   # 中等贡献阈值（默认0.4）
    top_n=10                # 返回top N指标
)
```

---

## 返回结果

`analyze_indicator_importance()` 返回一个字典，包含以下内容：

### 1. 按因子分类 (`by_factor`)

```python
{
    'Factor_1': {
        'high_contribution': {
            'indicators': ['GDP', 'INDPRO'],  # 载荷≥0.7
            'loadings': {'GDP': 0.85, 'INDPRO': 0.78}
        },
        'medium_contribution': {
            'indicators': ['PAYEMS', 'RSXFS'],  # 载荷0.4-0.7
            'loadings': {'PAYEMS': 0.65, 'RSXFS': 0.52}
        },
        'low_contribution': {
            'indicators': ['M1SL', 'M2SL'],  # 载荷<0.4
            'loadings': {'M1SL': 0.35, 'M2SL': 0.28}
        }
    }
}
```

### 2. 整体重要性排名 (`overall_importance`)

```python
{
    'GDP': {
        'max_loading': 0.85,          # 最大载荷
        'max_loading_factor': 'Factor_1',  # 最大载荷所在因子
        'mean_loading': 0.45,         # 平均载荷
        'rank': 1                     # 重要性排名
    }
}
```

### 3. 关键指标和冗余指标

```python
{
    'key_indicators': ['GDP', 'INDPRO', 'CPIAUCSL'],  # 高贡献指标
    'redundant_indicators': ['M1SL', 'BOGMBASE']     # 低贡献指标
}
```

---

## 可视化功能

### 绘制指标重要性排序图

```python
# 绘制第一个因子的指标重要性（Top 15）
fig = us_dfm.plot_indicator_importance(
    factor_index=0,      # 因子索引（0, 1, 2...）
    top_n=15,           # 显示前15个指标
    figsize=(12, 8)
)

# 保存图表
fig.savefig('indicator_importance.png', dpi=100)
```

图表特点：
- **红色**：高贡献指标（≥0.7）
- **橙色**：中贡献指标（0.4-0.7）
- **蓝色**：低贡献指标（<0.4）

---

## 实际应用示例

### 示例1：优化数据获取策略

```python
importance = us_dfm.analyze_indicator_importance()

key_indicators = importance['key_indicators']
redundant_indicators = importance['redundant_indicators']

print(f"关键指标（优先保证数据质量）：{key_indicators}")
print(f"冗余指标（可考虑删除）：{redundant_indicators}")

# 建议删除冗余指标
if redundant_indicators:
    print(f"\n建议删除以下指标以简化模型：")
    for indicator in redundant_indicators:
        print(f"  - {indicator}")
```

### 示例2：比较不同数据集的指标重要性

```python
# 数据集1：传统宏观数据
us_dfm1 = USDFM(n_factors=3)
us_dfm1.fit(traditional_data)
importance1 = us_dfm1.analyze_indicator_importance()

# 数据集2：添加另类数据后
us_dfm2 = USDFM(n_factors=5)
us_dfm2.fit(combined_data)
importance2 = us_dfm2.analyze_indicator_importance()

# 对比关键指标
key1 = set(importance1['key_indicators'])
key2 = set(importance2['key_indicators'])

print(f"传统数据关键指标：{key1}")
print(f"增强数据关键指标：{key2}")
print(f"新增关键指标：{key2 - key1}")
```

### 示例3：因子解释

```python
importance = us_dfm.analyze_indicator_importance()

# 查看每个因子的主要驱动指标
for factor_name, factor_data in importance['by_factor'].items():
    high = factor_data['high_contribution']['indicators']
    medium = factor_data['medium_contribution']['indicators']

    print(f"\n{factor_name} 主要驱动指标：")
    print(f"  高贡献：{high}")
    print(f"  中贡献：{medium}")

    # 解释经济含义
    if 'GDP' in high or 'INDPRO' in high:
        print(f"  → 该因子主要反映经济增长")
    if 'CPIAUCSL' in high or 'PCEPI' in high:
        print(f"  → 该因子主要反映通胀")
    if 'FEDFUNDS' in high or 'GS10' in high:
        print(f"  → 该因子主要反映流动性")
```

---

## 完整演示脚本

位置：`MacroTrading/demo_indicator_importance.py`

运行：
```bash
python MacroTrading/demo_indicator_importance.py
```

输出：
1. 控制台详细分析报告
2. 3个可视化图表（每个因子一个）
3. JSON格式的详细分析结果

---

## 技术细节

### 因子载荷的含义

因子载荷矩阵 Λ (25×3)：
```
              Factor_1  Factor_2  Factor_3
GDP             0.85      0.12      0.05
INDPRO          0.78      0.15      0.08
CPIAUCSL        0.20      0.88      0.05
FEDFUNDS        0.10      0.15      0.75
```

- **载荷绝对值越大**：指标与因子相关性越强
- **载荷接近0**：指标与因子几乎无关
- **正负号**：正相关或负相关

### 贡献度分类标准

| 分类 | 载荷绝对值 | 含义 |
|------|-----------|------|
| 高贡献 | ≥ 0.7 | 核心指标，强烈影响因子 |
| 中贡献 | 0.4 - 0.7 | 重要指标，对因子有明显贡献 |
| 低贡献 | < 0.4 | 边缘指标，贡献较小，可考虑删除 |

---

## 输出文件

运行演示脚本后生成的文件：

1. **indicator_importance_factor_1.png** - Factor_1 指标重要性图
2. **indicator_importance_factor_2.png** - Factor_2 指标重要性图
3. **indicator_importance_factor_3.png** - Factor_3 指标重要性图
4. **indicator_importance_analysis.json** - 详细分析结果（JSON格式）

---

## 注意事项

1. **模型必须先拟合**：调用 `analyze_indicator_importance()` 前必须先调用 `fit()`
2. **指标代码**：当前使用数字索引（0, 1, 2...），需要对照原始数据理解
3. **阈值选择**：默认阈值（0.7/0.4）是经验值，可根据具体数据调整
4. **数据质量**：分析结果受数据质量影响，缺失值过多可能导致偏差

---

## 扩展功能（未来）

1. **自动指标筛选**：根据重要性自动删除冗余指标
2. **指标名称映射**：将数字代码映射为可读的指标名称
3. **时序分析**：分析指标重要性的时间演变
4. **对比分析**：对比不同模型配置的指标重要性

---

## 作者与更新

- **添加时间**：2025-12-31
- **版本**：v1.0
- **位置**：`MacroTrading/models/dfm/base_dfm.py`

相关文件：
- `BaseDFM.analyze_indicator_importance()` - 核心方法
- `BaseDFM.plot_indicator_importance()` - 可视化方法
- `demo_indicator_importance.py` - 完整演示脚本
