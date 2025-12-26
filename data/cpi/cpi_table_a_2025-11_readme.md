# CPI Table A 数据说明 - 2025年11月

## 数据来源

- **机构**: U.S. Bureau of Labor Statistics (BLS)
- **数据发布**: Consumer Price Index Summary - 2025 M11 Results
- **原始网址**: https://www.bls.gov/news.release/cpi.nr0.htm
- **发布日期**: 2025年12月18日
- **数据文档**: USDL-25-1584

## 数据概述

本文件包含美国城市消费者消费者价格指数 (CPI-U) 的月度变化数据。

### CPI 指数说明

**CPI-U (Consumer Price Index for All Urban Consumers)**
- 衡量城市消费者为商品和服务支付的价格变化
- 代表超过90%的美国总人口
- 基期: 1982-84 = 100
- 2025年11月指数水平: 324.122

## 表格结构说明

### 文件: `cpi_table_a_2025-11.csv`

#### 列说明

1. **Category**: CPI 分类项目
   - 包含主要类别(All items, Food, Energy等)
   - 包含子类别(更详细的项目分类)

2. **May_2025 至 Nov_2025**: 经季节性调整的月度百分比变化
   - 单位: 百分比 (%)
   - 已进行季节性调整,消除常规季节性波动影响
   - **注意**: 2025年10月数据缺失,标记为 `NA`

3. **12_month_nov_2025**: 未调整的12个月百分比变化
   - 计算期间: 2024年11月 至 2025年11月
   - 未经季节性调整
   - 单位: 百分比 (%)

### 主要分类说明

| 分类 | 说明 |
|------|------|
| All items | 所有项目(总体CPI) |
| Food | 食品 |
| Food at home | 在家食品 |
| Food away from home | 外出就餐 |
| Energy | 能源 |
| Energy commodities | 能源商品(如汽油、燃油) |
| Energy services | 能源服务(如电力、天然气) |
| All items less food and energy | 剔除食品和能源的所有项目(核心CPI) |
| Shelter | 住房 |
| Medical care | 医疗保健 |

## 数据特殊情况

### 政府停摆影响 (2025年10月)

由于2025年政府拨款中断(lapse in appropriations),BLS未能收集10月份的调查数据。

- **影响**: 10月数据完全缺失,在CSV中标记为 `NA`
- **数据恢复**: 数据收集于2025年11月14日恢复
- **数据说明**: BLS无法追溯收集这些数据

### 部分项目有10月和11月数据

部分类别(如汽油)使用了非调查数据源,因此有10月和11月的独立数据点。

## 数据使用建议

### 数据分析

1. **短期趋势分析**: 使用经季节性调整的月度数据(May_2025 - Nov_2025)
   - 适合分析近期价格变化趋势
   - 已消除季节性因素影响

2. **长期趋势分析**: 使用12个月变化数据(12_month_nov_2025)
   - 适合分析同比通胀趋势
   - 反映年度价格变化

### 数据导入示例

#### Python (pandas)
```python
import pandas as pd

# 读取CSV文件,跳过注释行
df = pd.read_csv('cpi_table_a_2025-11.csv', comment='#')

# 查看数据
print(df.head())

# 筛选特定类别
food_inflation = df[df['Category'] == 'Food']
```

#### R
```r
# 读取CSV文件
df <- read.csv('cpi_table_a_2025-11.csv', comment.char = '#')

# 查看数据
head(df)

# 筛选特定类别
food_inflation <- df[df$Category == 'Food', ]
```

#### Excel
直接打开文件即可,注释行会自动显示为说明文本。

## 重要提示

1. **数据单位**: 所有数值均为百分比变化 (%)
2. **季节性调整**: 月度数据已调整,年度数据未调整
3. **缺失数据**: 10月数据用 `NA` 标记
4. **数据更新**: 下次CPI数据发布时间为 2026年1月13日

## 相关资源

- BLS CPI 主页: https://www.bls.gov/cpi/
- CPI 常见问题: https://www.bls.gov/cpi/questions-and-answers.htm
- 技术说明: https://www.bls.gov/cpi/cpifac.htm
- 政府停摆对CPI数据的影响: https://www.bls.gov/cpi/additional-resources/2025-federal-government-shutdown-impact-cpi.htm

## 更新记录

- **2025-12-26**: 初始版本,从BLS网站获取并整理2025年11月CPI数据

---

**数据说明文档生成时间**: 2025年12月26日
**数据最后更新**: 2025年12月18日 (BLS发布)
