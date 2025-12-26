# Indeptrader

Indeptrader 是一个独立的交易分析和宏观经济数据可视化平台,旨在帮助投资者更好地理解和分析经济指标。

## 项目概述

Indeptrader 提供了宏观经济数据的交互式可视化仪表板,展示关键经济指标的历史趋势和当前状态。项目采用纯前端技术栈,无需后端服务器即可运行。

## 目录结构

```
Indeptrader/
├── Macroeconomic/              # 宏观经济分析模块
│   ├── index.html             # 主页面入口
│   ├── css/
│   │   └── styles.css         # 样式文件
│   └── js/
│       ├── dashboard.js       # 仪表板逻辑
│       └── data.js            # 示例经济数据
├── CompanyAnalysis/           # 公司分析模块(开发中)
└── README.md                  # 项目文档
```

## 功能特性

### 宏观经济仪表板 (Macroeconomic Dashboard)

- **KPI 指标卡**: 展示四大核心经济指标的最新值和同比变化
  - GDP 增长率
  - 通货膨胀率 (CPI)
  - 失业率
  - 利率

- **交互式图表**: 使用 Chart.js 绘制时间序列数据
  - 平滑曲线图展示趋势
  - 悬停交互显示详细数据
  - 响应式设计适配不同屏幕

- **数据表格**: 可排序的历史数据表
  - 点击列标题进行升序/降序排序
  - 显示完整的月度经济数据

- **时间范围筛选**: 支持多种时间维度
  - 最近 1 年
  - 最近 3 年
  - 最近 5 年
  - 最近 10 年
  - 全部数据

## 技术栈

- **HTML5**: 页面结构
- **CSS3**: 样式和响应式设计
- **Vanilla JavaScript**: 核心逻辑(无框架依赖)
- **Chart.js 4.4.0**: 数据可视化库

## 快速开始

### 前置要求

- 现代浏览器(Chrome, Firefox, Safari, Edge)
- 本地 Web 服务器(可选,用于避免 CORS 问题)

### 安装与运行

1. **克隆或下载项目**

```bash
git clone <repository-url>
cd Indeptrader
```

2. **直接打开**

双击 `Macroeconomic/index.html` 文件在浏览器中打开

3. **使用本地服务器**(推荐)

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

然后在浏览器中访问: `http://localhost:8000`

## 数据说明

当前版本使用 2015-2024 年的模拟月度数据,包含以下指标:

- **GDP**: 国内生产总值增长率(%)
- **Inflation**: 通货膨胀率(消费者物价指数 CPI, %)
- **Unemployment**: 失业率(%)
- **Interest**: 联邦基金利率(%)

### 数据更新

要使用真实数据,请编辑 [js/data.js](Macroeconomic/js/data.js) 文件,修改 `economicData` 数组。数据格式如下:

```javascript
{
    date: 'YYYY-MM-DD',      // 日期(ISO 8601 格式)
    gdp: 2.5,                // GDP 增长率(%)
    inflation: 0.8,          // 通货膨胀率(%)
    unemployment: 5.7,       // 失业率(%)
    interest: 0.25          // 利率(%)
}
```

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
- FRED (Federal Reserve Economic Data)
- Bureau of Labor Statistics
- World Bank Open Data
- OECD 数据

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 未来计划

- [ ] 集成真实 API 数据源
- [ ] 添加更多经济指标(如 PMI、消费者信心等)
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

本项目采用 MIT 许可证 - 查看 LICENSE 文件了解详情

## 联系方式

如有问题或建议,请通过以下方式联系:
- 提交 Issue
- 发送 Pull Request

## 致谢

- [Chart.js](https://www.chartjs.org/) - 强大的图表库
- 经济数据来源: FRED, BLS 等

---

**最后更新**: 2024-12-26
**版本**: 0.1.0
