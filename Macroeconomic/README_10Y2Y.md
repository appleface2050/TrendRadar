# 10年期与2年期国债收益率利差分析系统

## 快速开始

### 方法 1：使用启动脚本（推荐）

**Linux / macOS:**
```bash
cd Macroeconomic
./start_server.sh
```

**Windows:**
```batch
cd Macroeconomic
start_server.bat
```

### 方法 2：手动启动 HTTP 服务器

```bash
cd Macroeconomic
python -m http.server 8088
```

然后在浏览器中访问：
```
http://localhost:8088/display/10y2y_spread.html
```

## 功能特性

### ✅ 四大核心分析功能

1. **长期趋势分析**
   - 49年历史数据可视化（1976-2025）
   - 动态颜色显示（正值绿色，负值红色）
   - 零线标注（倒挂分界线）
   - 支持缩放和平移

2. **收益率曲线倒挂分析**
   - 自动检测倒挂期间（连续负值 > 30天）
   - 显示倒挂持续天数
   - 标注最严重倒挂时间和幅度

3. **统计分析**
   - 基础统计：均值、中位数、极值、标准差
   - 分位数分析：25%, 50%, 75%, 90%, 95%
   - 滚动波动率（30日标准差）
   - 频率分布直方图

4. **对比分析**
   - 年代对比（1970s - 2020s）
   - 衰退前后对比（基于NBER衰退期）
   - 季节性分析（按月份）

## 数据更新

### 更新数据到最新

```bash
python Macroeconomic/fetch_data/get_fred_10y2y_spread_data.py
```

**注意**：数据将保存到根目录的 `data/raw/fred/fred_10y2y_spread/`，遵循项目的统一数据管理规范。

## 常见问题

### Q: 为什么不能直接双击打开 HTML 文件？

**A:** 浏览器的安全策略（CORS）会阻止通过 `file://` 协议加载本地数据文件。必须使用 HTTP 服务器。

### Q: 如何停止服务器？

**A:** 在运行服务器的终端按 `Ctrl+C`，或运行：
```bash
pkill -f 'python -m http.server 8088'
```

### Q: 页面显示 "CORS 错误" 怎么办？

**A:** 请确保通过 HTTP 服务器访问，而不是直接打开 HTML 文件。

### Q: 数据无法加载？

**A:** 检查以下几点：
1. 确保使用 HTTP 服务器访问
2. 检查数据文件是否存在：`data/raw/fred/fred_10y2y_spread/10y2y_spread.csv`（根目录）
3. 打开浏览器控制台查看详细错误信息（F12）

## 技术栈

- **Chart.js 4.4.1** - 图表渲染
- **chartjs-plugin-annotation** - 标注功能
- **chartjs-plugin-zoom** - 缩放平移
- **Vanilla JavaScript** - 无框架依赖
- **Python 3** - 数据获取

## 数据说明

- **数据源**: FRED (Federal Reserve Economic Data)
- **数据代码**: T10Y2Y
- **数据范围**: 1976-06-01 至 2025-12-24
- **数据点数**: 12,388条日度数据
- **数值范围**: -2.41% 至 2.91%
- **倒挂天数**: 约2,049天（16.5%）

## 浏览器兼容性

推荐使用以下浏览器的最新版本：
- ✅ Chrome/Edge
- ✅ Firefox
- ✅ Safari
- ❌ Internet Explorer（不支持）

## 文件结构

```
Macroeconomic/
├── display/
│   └── 10y2y_spread.html          # 主分析页面
├── js/10y2y_spread/
│   ├── data-processor.js          # 数据处理模块
│   ├── inversion-analyzer.js      # 倒挂检测模块
│   ├── statistics.js              # 统计分析模块
│   ├── comparison.js              # 对比分析模块
│   ├── chart-manager.js           # 图表管理模块
│   └── app.js                     # 主控制器
├── css/
│   └── 10y2y_spread.css           # 样式表
├── fetch_data/
│   └── get_fred_10y2y_spread_data.py  # 数据获取脚本
├── start_server.sh                # Linux/macOS 启动脚本
└── start_server.bat               # Windows 启动脚本

数据文件位置（根目录统一管理）：
data/
└── raw/
    └── fred/
        └── fred_10y2y_spread/
            └── 10y2y_spread.csv   # 数据源
```

## 使用技巧

1. **缩放图表**: 使用鼠标滚轮缩放，拖动平移
2. **查看数据**: 鼠标悬停在图表上显示详细数据
3. **导出数据**: 点击"导出数据"按钮下载当前筛选的数据
4. **切换时间范围**: 使用下拉框快速切换查看不同时间段
5. **调整数据粒度**: 可切换日度/周度/月度数据
