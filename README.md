# Indeptrader

Indeptrader 是一个独立的交易分析和宏观经济数据可视化平台，旨在帮助投资者更好地理解和分析经济指标。

## 项目简介

本项目用于可视化和分析美国宏观经济数据，包括:
- GDP 增长率
- 通货膨胀率(CPI)
- 失业率
- 利率
- 货币供应量(M1、M2)
- 10年期与2年期国债收益率利差分析
- 美国国债收益率期限结构分析

## 目录结构

```
Indeptrader/
├── Macroeconomic/              # 宏观经济分析模块
│   ├── index.html             # 主仪表板入口
│   ├── README_10Y2Y.md        # 10Y-2Y 利差分析详细文档
│   ├── display/               # 专题分析页面
│   │   ├── 10y2y_spread.html  # 10Y-2Y 利差分析页面
│   │   └── treasury_yield.html # 美国国债收益率分析页面
│   ├── css/
│   │   ├── dashboard.css      # 主仪表板样式
│   │   ├── styles.css         # 通用样式
│   │   ├── 10y2y_spread.css   # 利差分析样式
│   │   └── treasury_yield.css # 国债收益率样式
│   ├── js/
│   │   ├── app.js             # 主应用入口
│   │   ├── dashboard.js       # 仪表板逻辑
│   │   ├── data.js            # 示例经济数据
│   │   ├── 10y2y_spread/      # 利差分析模块
│   │   │   ├── app.js         # 应用主入口
│   │   │   ├── data-processor.js    # 数据处理
│   │   │   ├── inversion-analyzer.js # 倒挂分析
│   │   │   ├── statistics.js   # 统计计算
│   │   │   ├── comparison.js   # 对比分析
│   │   │   └── chart-manager.js # 图表管理
│   │   └── treasury_yield/    # 国债收益率模块
│   │       ├── app.js         # 应用主入口
│   │       ├── data-processor.js   # 数据处理
│   │       ├── curve-analyzer.js   # 曲线分析
│   │       ├── statistics.js   # 统计计算
│   │       └── chart-manager.js # 图表管理
│   ├── data/
│   │   ├── cpi/               # CPI 数据
│   │   │   ├── cpi_table_a_2025-11.csv         # CPI 数据表格
│   │   │   └── cpi_table_a_2025-11_readme.md   # 数据说明文档
│   │   ├── fred_monthly_money_supply/          # FRED 货币供应量数据
│   │   │   └── money_supply_m1_m2_monthly.csv  # M1、M2 货币供应量月度数据
│   │   ├── fred_10y2y_spread/  # FRED 利差数据
│   │   │   └── T10Y2Y.csv     # 10Y-2Y 利差日度数据
│   │   └── fred_treasury_yield/ # FRED 国债收益率数据
│   │       └── treasury_yield.csv # 多期限国债收益率数据
│   ├── fetch_data/            # 数据获取脚本
│   │   ├── get_fred_monthly_money_supply_data.py  # FRED API 货币供应量数据获取
│   │   ├── get_fred_10y2y_spread_data.py         # 利差数据获取脚本
│   │   └── get_fred_treasury_yield_data.py       # 国债收益率数据获取脚本
│   ├── start_server.sh        # Linux/macOS 启动脚本
│   └── start_server.bat       # Windows 启动脚本
├── CompanyAnalysis/           # 公司分析模块(开发中)
└── README.md                  # 项目文档
```

## 功能特性

### 1. 宏观经济仪表板

主仪表板提供全面的宏观经济数据可视化:

#### KPI 指标卡
实时显示 8 个关键经济指标:
- **GDP 增长率**: 国内生产总值同比增长率
- **CPI 通胀率**: 消费者价格指数变化
- **失业率**: 劳动力市场失业百分比
- **利率**: 联邦基金利率
- **M2 货币供应**: 广义货币供应量
- **PMI 指数**: 采购经理人指数
- **贸易差额**: 进出口贸易平衡
- **房价指数**: 房地产市场价格指标

#### 交互式图表
- **趋势图**: 多指标时间序列趋势对比
- **同比变化图**: 年度增长率可视化
- **分布图**: 数据分布特征分析
- 支持图表缩放、平移、标注等高级交互

#### 数据表格
- 支持排序和时间范围筛选
- 数据分页显示
- CSV 格式导出

#### 响应式设计
- 支持多种设备和屏幕尺寸
- 自适应布局优化

### 2. 10年期与2年期国债收益率利差分析

**独立的专题分析页面** ([display/10y2y_spread.html](Macroeconomic/display/10y2y_spread.html))

#### 长期趋势分析
- 展示 10Y-2Y 利差的完整历史趋势 (1976年至今，49年数据)
- 可视化收益率曲线的正常与倒挂状态
- 支持多时间范围筛选 (1年/5年/10年/全部)
- 支持多数据粒度 (日度/周度/月度)
- 零线标注，清晰区分正负利差

#### 倒挂分析
- 自动识别和分析收益率曲线倒挂
- 倒挂期检测和持续天数统计
- 历史倒挂期柱状图展示
- 倒挂天数超过30天的显著事件标记
- 经济衰退期标注

#### 波动率分析
- 30日滚动标准差计算
- 衡量市场波动程度
- 识别高波动和低波动时期

#### 分布统计
- 利差值频率分布直方图
- 均值和中位数标注
- 理解利差的分布特征

#### 对比分析
多维度对比功能:
- **年代对比**: 不同年代的利差表现
- **衰退对比**: 倒挂与经济衰退的关系
- **季节性**: 分析不同月份的利差规律

#### 交互式图表
- 基于 Chart.js 4.4.1 的高级图表
- 缩放和平移功能 (chartjs-plugin-zoom)
- 零线标注 (chartjs-plugin-annotation)
- 响应式设计，支持多设备访问

#### 统计数据表格
- 基础统计: 均值、中位数、标准差、最大/最小值
- 倒挂统计: 历史倒挂次数、最长持续天数、当前状态
- 分位数: 25%、50%、75% 分位数

#### 数据导出
- 支持导出当前筛选数据为 CSV 格式

### 3. 美国国债收益率分析

**新增的收益率分析模块** ([display/treasury_yield.html](Macroeconomic/display/treasury_yield.html))

#### 多期限收益率
- **关键期限**: 1年、2年、3年、5年、10年期国债收益率
- **历史数据**: 完整的收益率时间序列
- **实时更新**: 支持从 FRED API 获取最新数据

#### 收益率曲线分析
- **期限结构可视化**: 动态展示收益率曲线形态
- **曲线形态识别**: 正常、平坦、倒挂曲线
- **曲线变化追踪**: 随时间演化的动态分析

#### 利差分析
- **各期限与10年期利差**:
  - 10Y-1Y: 长短期利差
  - 10Y-2Y: 经典衰退指标
  - 10Y-3Y: 中期利差
  - 10Y-5Y: 中长期利差
- **利差趋势**: 各利差的历史变化
- **利差分布**: 统计特征分析

#### 波动率对比
- 各期限收益率的滚动标准差
- 波动率横向对比
- 高低波动期识别

#### 高级交互功能
- 图表缩放和平移
- 时间范围筛选
- 数据粒度选择 (日度/周度/月度)
- 多图表联动展示

### 4. CPI 数据分析

- 美国劳工统计局 (BLS) 官方 CPI 数据
- 包含详细的分类数据 (食品、能源、住房等)
- CSV 格式，便于分析和导入其他工具
- 完整的数据说明文档

### 5. 货币供应量数据

- 美联储 (FRED) 官方 M1、M2 货币供应量数据
- 脚本自动从 FRED API 获取最新数据
- CSV 格式存储，便于后续分析
- 支持自动更新和数据历史记录

## 技术栈

- **前端**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **图表库**: Chart.js 4.4.1
- **图表插件**:
  - chartjs-plugin-annotation 3.0.1 (图表标注)
  - chartjs-plugin-zoom 2.0.1 (缩放和平移)
- **数据格式**: JavaScript (JSON), CSV
- **数据获取**: Python 3.x with requests library

## 快速开始

### 方式一: 使用启动脚本 (推荐)

**Linux/macOS**:
```bash
cd Macroeconomic
bash start_server.sh
```

**Windows**:
```bash
cd Macroeconomic
start_server.bat
```

### 方式二: 在浏览器中直接打开

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

**国债收益率分析页面**:
```bash
open Macroeconomic/display/treasury_yield.html      # macOS
start Macroeconomic/display/treasury_yield.html     # Windows
xdg-open Macroeconomic/display/treasury_yield.html  # Linux
```

### 方式三: 本地服务器

如果需要通过本地服务器运行以避免 CORS 问题:

**使用 Python**:
```bash
cd Macroeconomic
python -m http.server 8000
```

**使用 Node.js**:
```bash
cd Macroeconomic
npx http-server -p 8000
```

然后在浏览器中访问: http://localhost:8000

### 导航提示

- 在主页面顶部的导航卡片中点击相应按钮可快速跳转到:
  - **10Y-2Y 利差** - 收益率曲线利差分析页面
  - **国债收益率** - 期限结构分析页面
- 各分析页面之间可以相互导航，方便在不同分析视图之间切换

## 数据说明

### Dashboard 数据

当前仪表板使用的是示例数据 (2015-2024年)，包含以下指标:
- **GDP Growth**: GDP 增长率 (%)
- **Inflation Rate**: 基于 CPI 的通货膨胀率 (%)
- **Unemployment Rate**: 失业率 (%)
- **Interest Rate**: 联邦基金利率 (%)
- **M2 Money Supply**: M2 货币供应量
- **PMI**: 采购经理人指数
- **Trade Balance**: 贸易差额
- **House Price Index**: 房价指数

#### 数据格式

数据存储在 [js/data.js](Macroeconomic/js/data.js)，格式如下:

```javascript
{
    date: 'YYYY-MM-DD',      // 日期 (ISO 8601 格式)
    gdp: 2.5,                // GDP 增长率 (%)
    inflation: 0.8,          // 通货膨胀率 (%)
    unemployment: 5.7,       // 失业率 (%)
    interest: 0.25,         // 利率 (%)
    m2: 14500.5,            // M2 货币供应量 (十亿美元)
    pmi: 52.3,              // PMI 指数
    tradeBalance: -45.2,    // 贸易差额 (十亿美元)
    hpi: 280.5              // 房价指数
}
```

### 10Y-2Y 利差数据

#### 数据来源

- **利差数据**: Federal Reserve Economic Data (FRED)
  - 数据代码: T10Y2Y (10-Year Treasury Constant Maturity Minus 2-Year)
  - 数据频率: 日度
  - 数据范围: 1976年至今 (49年历史数据)
  - 网址: https://fred.stlouisfed.org/series/T10Y2Y

#### 数据获取

运行数据获取脚本:
```bash
cd Macroeconomic/fetch_data
python get_fred_10y2y_spread_data.py
```

#### 经济意义

- **利差为正**: 正常的收益率曲线，长期利率高于短期利率，反映经济健康预期
- **利差为负 (倒挂)**: 收益率曲线倒挂，通常被视为经济衰退的领先指标
- **历史规律**: 美国过去的多次经济衰退前都出现过收益率曲线倒挂

### 国债收益率数据

#### 数据来源

- **收益率数据**: Federal Reserve Economic Data (FRED)
  - 数据代码:
    - DGS1: 1-Year Treasury Constant Maturity Rate
    - DGS2: 2-Year Treasury Constant Maturity Rate
    - DGS3: 3-Year Treasury Constant Maturity Rate
    - DGS5: 5-Year Treasury Constant Maturity Rate
    - DGS10: 10-Year Treasury Constant Maturity Rate
  - 数据频率: 日度
  - 数据范围: 1960年代至今
  - 网址: https://fred.stlouisfed.org

#### 数据获取

运行数据获取脚本:
```bash
cd Macroeconomic/fetch_data
python get_fred_treasury_yield_data.py
```

#### 数据格式

数据文件: [data/fred_treasury_yield/treasury_yield.csv](Macroeconomic/data/fred_treasury_yield/treasury_yield.csv)

```csv
Date,1Y,2Y,3Y,5Y,10Y
2025-12-22,4.25,4.35,4.42,4.51,4.62
...
```

### CPI 数据

CPI 数据文件位于 [Macroeconomic/data/cpi/](Macroeconomic/data/cpi/) 目录:

- **cpi_table_a_2025-11.csv**: 2025年11月 CPI Table A 数据
  - 包含 20 个 CPI 分类项目
  - 月度变化数据 (经季节性调整)
  - 12个月变化数据 (未经调整)
  - 完整的元数据注释

- **cpi_table_a_2025-11_readme.md**: 详细的数据说明文档
  - 数据来源和说明
  - 表格结构解释
  - 使用示例代码 (Python、R、Excel)

#### 数据来源

- **CPI 数据**: U.S. Bureau of Labor Statistics (BLS)
  - 网址: https://www.bls.gov/news.release/cpi.nr0.htm
  - 发布日期: 2025-12-18

### 货币供应量数据

货币供应量数据文件位于 [Macroeconomic/data/fred_monthly_money_supply/](Macroeconomic/data/fred_monthly_money_supply/) 目录:

- **money_supply_m1_m2_monthly.csv**: M1、M2 货币供应量月度数据
  - **M1**: 狭义货币供应量，包括流通中的货币 + 活期存款
  - **M2**: 广义货币供应量，包括 M1 + 储蓄存款 + 小额定期存款
  - 数据来源: 美联储经济数据 (FRED)
  - 单位: 十亿美元 (Billions of Dollars)
  - 频率: 月度数据
  - 包含数据获取时间戳

#### 数据获取脚本

```bash
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

### 核心设计原则

#### 模块化架构
- 每个分析页面采用独立的模块化设计
- 功能解耦: 数据处理、统计分析、图表管理、UI控制分离
- 便于维护和扩展

#### 状态管理
- 集中式状态管理
- 响应式数据更新
- 高效的缓存机制

#### 性能优化
- 懒加载: 按需加载数据和图表
- 数据降采样: 大数据集自动优化 (超过3000点)
- 图表渲染优化

### 核心文件说明

#### 主仪表板模块

- **[index.html](Macroeconomic/index.html)**: 主页面结构
  - KPI 卡片展示区域
  - 图表容器
  - 数据表格
  - 引入外部依赖

- **[js/app.js](Macroeconomic/js/app.js)**: 主应用控制器
  - 应用初始化
  - 全局状态管理
  - 组件协调

- **[js/dashboard.js](Macroeconomic/js/dashboard.js)**: 仪表板逻辑
  - `initializeDashboard()`: 初始化仪表板
  - `updateKPIs()`: 更新 KPI 指标卡
  - `initializeCharts()`: 创建和配置图表
  - `populateTable()`: 填充数据表格
  - `filterDataByYears()`: 时间范围过滤
  - `setupEventListeners()`: 事件监听器设置
  - `updateDashboard()`: 刷新所有视图

- **[js/data.js](Macroeconomic/js/data.js)**: 数据存储
  - 存储宏观经济数据
  - 包含 2015-2024 年的月度数据
  - 可扩展为动态数据加载

#### 利差分析模块

- **[display/10y2y_spread.html](Macroeconomic/display/10y2y_spread.html)**: 利差分析页面

- **[js/10y2y_spread/app.js](Macroeconomic/js/10y2y_spread/app.js)**: 主控制器
  - 应用初始化和配置
  - 模块协调和状态管理
  - 事件处理

- **[js/10y2y_spread/data-processor.js](Macroeconomic/js/10y2y_spread/data-processor.js)**: 数据处理
  - 数据加载和解析
  - 时间范围筛选
  - 数据粒度转换 (日度/周度/月度)
  - 降采样处理

- **[js/10y2y_spread/inversion-analyzer.js](Macroeconomic/js/10y2y_spread/inversion-analyzer.js)**: 倒挂分析
  - 倒挂期检测
  - 持续天数统计
  - 倒挂事件汇总

- **[js/10y2y_spread/statistics.js](Macroeconomic/js/10y2y_spread/statistics.js)**: 统计计算
  - 基础统计量计算
  - 滚动标准差
  - 分位数分析

- **[js/10y2y_spread/comparison.js](Macroeconomic/js/10y2y_spread/comparison.js)**: 对比分析
  - 年代对比
  - 衰退对比
  - 季节性分析

- **[js/10y2y_spread/chart-manager.js](Macroeconomic/js/10y2y_spread/chart-manager.js)**: 图表管理
  - 图表创建和配置
  - 插件管理
  - 图表更新和销毁

#### 国债收益率模块

- **[display/treasury_yield.html](Macroeconomic/display/treasury_yield.html)**: 收益率分析页面

- **[js/treasury_yield/app.js](Macroeconomic/js/treasury_yield/app.js)**: 主控制器

- **[js/treasury_yield/data-processor.js](Macroeconomic/js/treasury_yield/data-processor.js)**: 数据处理

- **[js/treasury_yield/curve-analyzer.js](Macroeconomic/js/treasury_yield/curve-analyzer.js)**: 曲线分析
  - 收益率曲线形态识别
  - 利差计算
  - 曲线变化追踪

- **[js/treasury_yield/statistics.js](Macroeconomic/js/treasury_yield/statistics.js)**: 统计计算

- **[js/treasury_yield/chart-manager.js](Macroeconomic/js/treasury_yield/chart-manager.js)**: 图表管理

#### 样式系统

- **[css/dashboard.css](Macroeconomic/css/dashboard.css)**: 主仪表板样式
  - KPI 卡片样式
  - 图表布局
  - 响应式设计

- **[css/styles.css](Macroeconomic/css/styles.css)**: 通用样式
  - 全局样式
  - 颜色变量
  - 动画效果

- **[css/10y2y_spread.css](Macroeconomic/css/10y2y_spread.css)**: 利差分析样式

- **[css/treasury_yield.css](Macroeconomic/css/treasury_yield.css)**: 收益率分析样式

## 自定义和扩展

### 修改样式

编辑相应的 CSS 文件自定义:
- 配色方案 (当前为紫色渐变)
- 布局和间距
- 字体和排版
- 响应式断点

### 添加新的经济指标

1. 在 [data.js](Macroeconomic/js/data.js) 中添加新字段
2. 在 [index.html](Macroeconomic/index.html) 中添加新的 KPI 卡片和图表容器
3. 在 [dashboard.js](Macroeconomic/js/dashboard.js) 中添加相应的更新和图表初始化逻辑

### 添加新的分析模块

参考现有模块结构 (10y2y_spread 或 treasury_yield):

1. 创建独立的页面 HTML 文件
2. 创建模块目录和相应 JS 文件:
   - app.js: 主控制器
   - data-processor.js: 数据处理
   - statistics.js: 统计分析
   - chart-manager.js: 图表管理
   - [特定分析].js: 专项分析逻辑
3. 创建专用的 CSS 样式文件
4. 在主仪表板添加导航链接

### 集成真实数据源

可以替换静态数据，集成以下数据源:
- **FRED** (Federal Reserve Economic Data) - 已集成
- **Bureau of Labor Statistics** - 已集成
- **World Bank Open Data**
- **OECD 数据**

### 配置 FRED API

在数据获取脚本中配置 API 密钥:

```python
# 设置 FRED API 密钥
FRED_API_KEY = 'your_api_key_here'

# 或通过环境变量
import os
FRED_API_KEY = os.environ.get('FRED_API_KEY')
```

获取 API 密钥: https://fred.stlouisfed.org/docs/api/api_key.html

## 数据更新

### 自动更新脚本

所有数据获取脚本都支持增量更新:

```bash
# 更新利差数据
cd Macroeconomic/fetch_data
python get_fred_10y2y_spread_data.py

# 更新国债收益率数据
python get_fred_treasury_yield_data.py

# 更新货币供应量数据
python get_fred_monthly_money_supply_data.py
```

### 定时更新

可以设置 cron 任务 (Linux/macOS) 或任务计划程序 (Windows) 定期自动更新数据。

## 未来计划

- [ ] 集成更多实时 API 数据源
- [ ] 添加更多国债收益率利差分析 (如 10Y-3M、30Y-2Y 等)
- [ ] 集成经济衰退日历和事件标注
- [ ] 添加数据预测功能 (时间序列预测)
- [ ] 支持多国/地区数据对比
- [ ] 开发公司分析模块
- [ ] 添加技术指标分析
- [ ] 实现数据预警和通知功能
- [ ] 开发移动端应用
- [ ] 添加用户自定义指标功能

## 详细文档

- [10Y-2Y 利差分析详细说明](Macroeconomic/README_10Y2Y.md)

## 常见问题

### Q: 为什么有些图表显示"暂无数据"?

A: 可能的原因:
1. 数据文件未加载或路径错误
2. 浏览器缓存问题 - 尝试清除缓存或使用硬刷新 (Ctrl+Shift+R)
3. CORS 问题 - 使用本地服务器而非直接打开文件

### Q: 如何添加自定义的数据源?

A: 参考现有模块的数据处理流程:
1. 创建数据获取脚本 (参考 fetch_data 目录)
2. 创建数据处理器 (参考 data-processor.js)
3. 实现图表管理器 (参考 chart-manager.js)
4. 创建独立的 HTML 页面

### Q: 图表缩放功能如何使用?

A:
- **缩放**: 鼠标滚轮 (桌面端) 或双指捏合 (触屏设备)
- **平移**: 点击并拖动图表
- **重置**: 双击图表或使用重置按钮 (如果提供)

### Q: 数据更新频率是多少?

A:
- **FRED 数据**: 根据指标不同，日度、周度或月度更新
- **CPI 数据**: 美国劳工统计局每月发布
- 建议每周运行一次数据更新脚本

---

**最后更新**: 2025-12-26
**版本**: 0.5.0
