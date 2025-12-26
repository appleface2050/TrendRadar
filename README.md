# Macroeconomic Data Dashboard

一个宏观经济数据可视化仪表板，展示关键经济指标的趋势分析。

## 项目简介

本项目用于可视化和分析美国宏观经济数据，包括：
- GDP 增长率
- 通货膨胀率（CPI）
- 失业率
- 利率

## 项目结构

```
macroeconomic/
├── index.html              # 主页面
├── css/
│   └── styles.css          # 样式文件
├── js/
│   ├── data.js             # 经济数据
│   └── dashboard.js        # Dashboard 逻辑
├── data/
│   └── cpi/                # CPI 数据
│       ├── cpi_table_a_2025-11.csv         # CPI 数据表格
│       └── cpi_table_a_2025-11_readme.md   # 数据说明文档
└── README.md               # 项目说明
```

## 功能特性

### 1. 数据仪表板
- 实时显示关键经济指标（KPI 卡片）
- 交互式图表展示经济趋势
- 数据表格支持排序和时间范围筛选
- 响应式设计，支持多种设备

### 2. CPI 数据分析
- 美国劳工统计局（BLS）官方 CPI 数据
- 包含详细的分类数据（食品、能源、住房等）
- CSV 格式，便于分析和导入其他工具
- 完整的数据说明文档

## 快速开始

### 在浏览器中打开

直接打开 `index.html` 文件即可查看仪表板：

```bash
# 在项目根目录下
open index.html        # macOS
start index.html       # Windows
xdg-open index.html    # Linux
```

### 本地服务器（可选）

如果需要通过本地服务器运行：

```bash
# 使用 Python 3
python -m http.server 8000

# 使用 Python 2
python -m SimpleHTTPServer 8000

# 使用 Node.js
npx http-server
```

然后访问：http://localhost:8000

## 数据说明

### Dashboard 数据

当前仪表板使用的是示例数据（2015-2024年），包含以下指标：
- **GDP Growth**: 季度 GDP 增长率
- **Inflation Rate**: 基于 CPI 的通货膨胀率
- **Unemployment Rate**: 失业率
- **Interest Rate**: 联邦基金利率

### CPI 数据

CPI 数据文件位于 `data/cpi/` 目录：

- **cpi_table_a_2025-11.csv**: 2025年11月 CPI Table A 数据
  - 包含 20 个 CPI 分类项目
  - 月度变化数据（经季节性调整）
  - 12个月变化数据（未经调整）
  - 完整的元数据注释

- **cpi_table_a_2025-11_readme.md**: 详细的数据说明文档
  - 数据来源和说明
  - 表格结构解释
  - 使用示例代码（Python、R、Excel）

### 数据来源

- **CPI 数据**: U.S. Bureau of Labor Statistics (BLS)
  - 网址: https://www.bls.gov/news.release/cpi.nr0.htm
  - 发布日期: 2025-12-18

## 技术栈

- **前端**: HTML5, CSS3, JavaScript (ES6+)
- **图表库**: Chart.js 4.4.0
- **数据格式**: JavaScript (JSON), CSV

## 未来计划

- [ ] 集成实时 CPI 数据到仪表板
- [ ] 添加数据自动更新功能
- [ ] 扩展更多经济指标
- [ ] 添加数据导出功能
- [ ] 支持多国数据对比

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过 GitHub Issues 联系。

---

**最后更新**: 2025-12-26
