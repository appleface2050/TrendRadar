# Indeptrader

Indeptrader 是一个独立的交易分析和宏观经济数据可视化平台,旨在帮助投资者更好地理解和分析经济指标。

## 项目简介

本项目用于可视化和分析美国宏观经济数据,包括:
- GDP 增长率
- 通货膨胀率(CPI)
- 失业率
- 利率
- 货币供应量(M1、M2)

## 目录结构

```
Indeptrader/
├── Macroeconomic/              # 宏观经济分析模块
│   ├── index.html             # 主页面入口
│   ├── css/
│   │   └── styles.css         # 样式文件
│   ├── js/
│   │   ├── dashboard.js       # 仪表板逻辑
│   │   └── data.js            # 示例经济数据
│   ├── data/
│   │   ├── cpi/               # CPI 数据
│   │   │   ├── cpi_table_a_2025-11.csv         # CPI 数据表格
│   │   │   └── cpi_table_a_2025-11_readme.md   # 数据说明文档
│   │   └── fred_monthly_money_supply/          # FRED 货币供应量数据
│   │       └── money_supply_m1_m2_monthly.csv  # M1、M2 货币供应量月度数据
│   └── fetch_data/            # 数据获取脚本
│       └── get_fred_monthly_money_supply_data.py  # FRED API 数据获取脚本
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

### 3. 货币供应量数据
- 美联储(FRED)官方 M1、M2 货币供应量数据
- 脚本自动从 FRED API 获取最新数据
- CSV 格式存储,便于后续分析
- 支持自动更新和数据历史记录

## 技术栈

- **前端**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **图表库**: Chart.js 4.4.0
- **数据格式**: JavaScript (JSON), CSV

## 快速开始

### 在浏览器中打开

直接打开 [Macroeconomic/index.html](Macroeconomic/index.html) 文件即可查看仪表板:

```bash
# 使用命令行打开
open Macroeconomic/index.html        # macOS
start Macroeconomic/index.html       # Windows
xdg-open Macroeconomic/index.html    # Linux
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

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 未来计划

- [ ] 集成真实 API 数据源(FRED, BLS)
- [ ] 集成实时 CPI 数据到仪表板
- [ ] 添加数据自动更新功能
- [ ] 扩展更多经济指标(如 PMI、消费者信心等)
- [ ] 实现数据导出功能(CSV, Excel)
- [ ] 开发公司分析模块
- [ ] 添加数据预测功能
- [ ] 支持多国/地区数据对比

## 贡献指南

欢迎贡献! 请遵循以下步骤:

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证

## 致谢

- [Chart.js](https://www.chartjs.org/) - 强大的图表库
- 经济数据来源: FRED, BLS 等

---

**最后更新**: 2025-12-26
**版本**: 0.1.0
