# Indeptrader

Indeptrader 是一个独立的交易分析和宏观经济数据可视化平台,旨在帮助投资者更好地理解和分析经济指标。

## 项目简介

本项目用于可视化和分析美国宏观经济数据,包括:
- GDP 增长率
- 通货膨胀率(CPI)
- 失业率
- 利率
- 货币供应量(M1、M2)
- 10年期与2年期国债收益率利差分析

## 目录结构

```
Indeptrader/
├── Macroeconomic/              # 宏观经济分析模块
│   ├── index.html             # 主页面入口
│   ├── display/               # 专题分析页面
│   │   └── 10y2y_spread.html  # 10Y-2Y 利差分析页面
│   ├── css/
│   │   ├── dashboard.css      # 主页面样式
│   │   └── 10y2y_spread.css   # 利差分析样式
│   ├── js/
│   │   ├── dashboard.js       # 仪表板逻辑
│   │   ├── data.js            # 示例经济数据
│   │   └── 10y2y_spread/      # 利差分析模块
│   │       ├── app.js         # 应用主入口
│   │       ├── data-processor.js    # 数据处理
│   │       ├── inversion-analyzer.js # 倒挂分析
│   │       ├── statistics.js   # 统计计算
│   │       ├── comparison.js   # 对比分析
│   │       └── chart-manager.js # 图表管理
│   ├── data/
│   │   ├── cpi/               # CPI 数据
│   │   │   ├── cpi_table_a_2025-11.csv         # CPI 数据表格
│   │   │   └── cpi_table_a_2025-11_readme.md   # 数据说明文档
│   │   ├── fred_monthly_money_supply/          # FRED 货币供应量数据
│   │   │   └── money_supply_m1_m2_monthly.csv  # M1、M2 货币供应量月度数据
│   │   └── fred_10y2y_spread/  # FRED 利差数据
│   │       └── T10Y2Y.csv     # 10Y-2Y 利差日度数据
│   └── fetch_data/            # 数据获取脚本
│       ├── get_fred_monthly_money_supply_data.py  # FRED API 数据获取脚本
│       └── get_fred_10y2y_spread_data.py         # 利差数据获取脚本
├── CompanyAnalysis/           # 公司分析模块(开发中)
└── README.md                  # 项目文档
```

## 功能特性

### 1. 数据仪表板
- **KPI 指标卡**: 实时显示关键经济指标的最新值和同比变化
- **交互式图表**: 使用 Chart.js 绘制平滑的时间序列趋势图
- **数据表格**: 支持排序和时间范围筛选
- **时间范围筛选**: 支持 1/3/5/10 年或全部数据
- **响应式设计**: 支持多种设备和屏幕尺寸

### 2. CPI 数据分析
- 美国劳工统计局(BLS)官方 CPI 数据
- 包含详细的分类数据(食品、能源、住房等)
- CSV 格式,便于分析和导入其他工具
- 完整的数据说明文档

### 3. 10年期与2年期国债收益率利差分析

**独立的专题分析页面** ([display/10y2y_spread.html](Macroeconomic/display/10y2y_spread.html)):

- **长期趋势分析**: 展示 10Y-2Y 利差的完整历史趋势
  - 可视化收益率曲线的正常与倒挂状态
  - 支持多时间范围筛选(1年/5年/10年/全部)
  - 支持多数据粒度(日度/周度/月度)
  - 零线标注，清晰区分正负利差

- **倒挂分析**: 自动识别和分析收益率曲线倒挂
  - 倒挂期检测和持续天数统计
  - 历史倒挂期柱状图展示
  - 倒挂天数超过30天的显著事件标记

- **波动率分析**: 30日滚动标准差计算
  - 衡量市场波动程度
  - 识别高波动和低波动时期

- **分布统计**: 利差值频率分布直方图
  - 均值和中位数标注
  - 理解利差的分布特征

- **对比分析**: 多维度对比功能
  - 年代对比: 不同年代的利差表现
  - 衰退对比: 倒挂与经济衰退的关系
  - 季节性: 分析不同月份的利差规律

- **交互式图表**: 基于 Chart.js 的高级图表
  - 缩放和平移功能(chartjs-plugin-zoom)
  - 零线标注(chartjs-plugin-annotation)
  - 响应式设计，支持多设备访问

- **统计数据表格**: 完整的统计指标
  - 基础统计: 均值、中位数、标准差、最大/最小值
  - 倒挂统计: 历史倒挂次数、最长持续天数、当前状态
  - 分位数: 25%、50%、75% 分位数

- **数据导出**: 支持导出分析结果为 CSV 格式

#### 数据来源

- **利差数据**: Federal Reserve Economic Data (FRED)
  - 数据代码: T10Y2Y (10-Year Treasury Constant Maturity Minus 2-Year)
  - 数据频率: 日度
  - 数据范围: 1976年至今
  - 网址: https://fred.stlouisfed.org/series/T10Y2Y

#### 经济意义

- **利差为正**: 正常的收益率曲线，长期利率高于短期利率，反映经济健康预期
- **利差为负(倒挂)**: 收益率曲线倒挂，通常被视为经济衰退的领先指标
- **历史规律**: 美国过去的多次经济衰退前都出现过收益率曲线倒挂

### 4. 货币供应量数据
- 美联储(FRED)官方 M1、M2 货币供应量数据
- 脚本自动从 FRED API 获取最新数据
- CSV 格式存储,便于后续分析
- 支持自动更新和数据历史记录

## 技术栈

- **前端**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **图表库**: Chart.js 4.4.1
- **图表插件**:
  - chartjs-plugin-annotation 3.0.1 (图表标注)
  - chartjs-plugin-zoom 2.0.1 (缩放和平移)
- **数据格式**: JavaScript (JSON), CSV

## 快速开始

### 在浏览器中打开

直接打开以下文件之一即可查看不同页面:

**主页面 (宏观经济仪表板)**:
```bash
# 使用命令行打开
open Macroeconomic/index.html        # macOS
start Macroeconomic/index.html       # Windows
xdg-open Macroeconomic/index.html    # Linux
```

**利差分析页面**:
```bash
open Macroeconomic/display/10y2y_spread.html        # macOS
start Macroeconomic/display/10y2y_spread.html       # Windows
xdg-open Macroeconomic/display/10y2y_spread.html    # Linux
```

### 本地服务器(推荐)

如果需要通过本地服务器运行以避免 CORS 问题:

使用 Python:
```bash
cd Macroeconomic
python -m http.server 8000
```

使用 Node.js:
```bash
cd Macroeconomic
npx http-server -p 8000
```

然后在浏览器中访问: http://localhost:8000

**导航提示**:
- 在主页面顶部的导航卡片中点击 "10Y-2Y 利差" 按钮可快速跳转到利差分析页面
- 两个页面之间可以相互导航，方便在不同分析视图之间切换

## 数据说明

### Dashboard 数据

当前仪表板使用的是示例数据(2015-2024年),包含以下指标:
- **GDP Growth**: GDP 增长率(%)
- **Inflation Rate**: 基于 CPI 的通货膨胀率(%)
- **Unemployment Rate**: 失业率(%)
- **Interest Rate**: 联邦基金利率(%)

#### 数据格式

数据存储在 [js/data.js](Macroeconomic/js/data.js),格式如下:

```javascript
{
    date: 'YYYY-MM-DD',      // 日期(ISO 8601 格式)
    gdp: 2.5,                // GDP 增长率(%)
    inflation: 0.8,          // 通货膨胀率(%)
    unemployment: 5.7,       // 失业率(%)
    interest: 0.25          // 利率(%)
}
```

### CPI 数据

CPI 数据文件位于 [Macroeconomic/data/cpi/](Macroeconomic/data/cpi/) 目录:

- **cpi_table_a_2025-11.csv**: 2025年11月 CPI Table A 数据
  - 包含 20 个 CPI 分类项目
  - 月度变化数据(经季节性调整)
  - 12个月变化数据(未经调整)
  - 完整的元数据注释

- **cpi_table_a_2025-11_readme.md**: 详细的数据说明文档
  - 数据来源和说明
  - 表格结构解释
  - 使用示例代码(Python、R、Excel)

#### 数据来源

- **CPI 数据**: U.S. Bureau of Labor Statistics (BLS)
  - 网址: https://www.bls.gov/news.release/cpi.nr0.htm
  - 发布日期: 2025-12-18

### 货币供应量数据

货币供应量数据文件位于 [Macroeconomic/data/fred_monthly_money_supply/](Macroeconomic/data/fred_monthly_money_supply/) 目录:

- **money_supply_m1_m2_monthly.csv**: M1、M2 货币供应量月度数据
  - **M1**: 狭义货币供应量,包括流通中的货币+活期存款
  - **M2**: 广义货币供应量,包括 M1 + 储蓄存款+小额定期存款
  - 数据来源: 美联储经济数据(FRED)
  - 单位: 十亿美元(Billions of Dollars)
  - 频率: 月度数据
  - 包含数据获取时间戳

#### 数据获取脚本

数据获取脚本位于 [fetch_data/get_fred_monthly_money_supply_data.py](Macroeconomic/fetch_data/get_fred_monthly_money_supply_data.py):

```bash
# 运行脚本获取最新数据
cd Macroeconomic/fetch_data
python get_fred_monthly_money_supply_data.py
```

脚本功能:
- 从 FRED API 获取 M1、M2 货币供应量数据
- 自动保存为 CSV 格式
- 包含完整的错误处理和日志记录
- 支持 FRED API 密钥配置

#### 数据来源

- **货币供应量数据**: Federal Reserve Economic Data (FRED)
  - **M1 数据**: https://fred.stlouisfed.org/graph/fredgraph.csv?id=M1SL
  - **M2 数据**: https://fred.stlouisfed.org/graph/fredgraph.csv?id=M2SL
  - 数据发布机构: Federal Reserve Board
  - 数据频率: 每周/每月

## 项目架构

### 核心文件说明

#### [index.html](Macroeconomic/index.html)
- 主页面结构
- KPI 卡片展示区域
- 图表容器
- 数据表格
- 引入外部依赖(CSS, JS, Chart.js)

#### [js/dashboard.js](Macroeconomic/js/dashboard.js)
主要功能模块:
- `initializeDashboard()`: 初始化仪表板
- `updateKPIs()`: 更新 KPI 指标卡
- `initializeCharts()`: 创建和配置图表
- `populateTable()`: 填充数据表格
- `filterDataByYears()`: 时间范围过滤
- `setupEventListeners()`: 事件监听器设置
- `updateDashboard()`: 刷新所有视图

#### [js/data.js](Macroeconomic/js/data.js)
- 存储宏观经济数据
- 包含 2015-2024 年的月度数据
- 可扩展为动态数据加载

#### [css/styles.css](Macroeconomic/css/styles.css)
- 响应式布局设计
- 渐变配色方案
- 悬停效果和过渡动画
- 移动端适配(@media queries)

## 自定义和扩展

### 修改样式

编辑 [css/styles.css](Macroeconomic/css/styles.css) 自定义:
- 配色方案(当前为紫色渐变)
- 布局和间距
- 字体和排版
- 响应式断点

### 添加新的经济指标

1. 在 [data.js](Macroeconomic/js/data.js) 中添加新字段
2. 在 [index.html](Macroeconomic/index.html) 中添加新的 KPI 卡片和图表容器
3. 在 [dashboard.js](Macroeconomic/js/dashboard.js) 中添加相应的更新和图表初始化逻辑

### 集成真实数据源

可以替换静态数据,集成以下数据源:
- **FRED** (Federal Reserve Economic Data)
- **Bureau of Labor Statistics**
- **World Bank Open Data**
- **OECD 数据**

## 未来计划

- [ ] 集成真实 API 数据源(FRED, BLS)
- [ ] 集成实时 CPI 数据到仪表板
- [ ] 添加数据自动更新功能
- [ ] 扩展更多经济指标(如 PMI、消费者信心等)
- [x] 实现数据导出功能(CSV, Excel) - 10Y-2Y 利差分析已完成
- [ ] 开发公司分析模块
- [ ] 添加数据预测功能
- [ ] 支持多国/地区数据对比
- [ ] 添加更多国债收益率利差分析(如 10Y-3M、30Y-2Y 等)
- [ ] 集成经济衰退日历和事件标注


---

**最后更新**: 2025-12-26
**版本**: 0.3.0
