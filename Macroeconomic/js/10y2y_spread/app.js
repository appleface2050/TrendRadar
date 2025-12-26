/**
 * 10年期与2年期国债收益率利差分析 - 主控制器
 * 协调各个模块，处理用户交互
 */

(function() {
    'use strict';

    // 应用状态
    const state = {
        rawData: [],
        currentData: [],
        timeRange: 'all',
        granularity: 'day',
        comparisonTab: 'decade',
        isLoading: false
    };

    /**
     * 初始化应用
     */
    async function init() {
        try {
            showLoading(true);

            // 加载数据
            await loadData();

            // 初始化UI
            initUI();

            // 更新所有图表和统计
            updateAll();

            showLoading(false);
        } catch (error) {
            console.error('初始化失败:', error);
            showLoading(false);
            showError('加载数据失败: ' + error.message);
        }
    }

    /**
     * 加载数据
     */
    async function loadData() {
        try {
            state.rawData = await DataProcessor.loadCSVData();
            state.currentData = state.rawData;
            console.log('数据加载成功:', state.rawData.length, '条记录');
        } catch (error) {
            console.error('加载数据失败:', error);
            throw error;
        }
    }

    /**
     * 初始化UI事件监听
     */
    function initUI() {
        // 时间范围选择
        const timeRangeSelect = document.getElementById('timeRange');
        if (timeRangeSelect) {
            timeRangeSelect.addEventListener('change', (e) => {
                state.timeRange = e.target.value;
                handleTimeRangeChange();
            });
        }

        // 数据粒度选择
        const granularitySelect = document.getElementById('granularity');
        if (granularitySelect) {
            granularitySelect.addEventListener('change', (e) => {
                state.granularity = e.target.value;
                handleGranularityChange();
            });
        }

        // 重置缩放按钮
        const resetZoomBtn = document.getElementById('resetZoom');
        if (resetZoomBtn) {
            resetZoomBtn.addEventListener('click', () => {
                ChartManager.resetZoom('trend');
            });
        }

        // 导出按钮
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', exportData);
        }

        // 对比分析标签切换
        const tabButtons = document.querySelectorAll('.tab-btn');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                handleComparisonTabChange(tab);
            });
        });
    }

    /**
     * 更新所有图表和统计
     */
    function updateAll() {
        // 处理数据
        let data = state.rawData;

        // 时间范围筛选
        data = DataProcessor.filterByTimeRange(data, state.timeRange);

        // 数据聚合
        data = DataProcessor.aggregateData(data, state.granularity);

        // 降采样（大数据集）
        if (data.length > 3000) {
            data = DataProcessor.downsample(data, 3000);
        }

        state.currentData = data;

        // 更新KPI卡片
        updateKPICards();

        // 更新图表
        updateCharts(data);

        // 更新统计表格
        updateStatisticsTables();
    }

    /**
     * 更新KPI卡片
     */
    function updateKPICards() {
        const data = state.currentData;
        if (!data || data.length === 0) return;

        // 当前值
        const currentValue = data[data.length - 1].value;
        updateKPI('currentValue', currentValue.toFixed(2), currentValue >= 0 ? 'positive' : 'negative');

        // 历史均值
        const stats = Statistics.calculateBasicStats(data);
        if (stats) {
            updateKPI('meanValue', stats.mean.toFixed(2));
        }

        // 倒挂天数
        const inversionStats = InversionAnalyzer.calculateInversionStats(data);
        updateKPI('inversionDays', inversionStats.inversionDays.toString());

        // 波动率（标准差）
        if (stats) {
            updateKPI('volatility', stats.stdDev.toFixed(2));
        }
    }

    /**
     * 更新单个KPI卡片
     */
    function updateKPI(elementId, value, status = '') {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
            element.className = 'kpi-value ' + status;
        }
    }

    /**
     * 更新所有图表
     */
    function updateCharts(data) {
        if (!data || data.length === 0) return;

        // 1. 趋势图
        const inversionAnnotations = InversionAnalyzer.prepareInversionAnnotations(data, 30);
        ChartManager.initTrendChart('trendChart', data, inversionAnnotations);

        // 2. 倒挂分析图
        const inversionPeriods = InversionAnalyzer.detectInversions(data, 30);
        if (inversionPeriods.length > 0) {
            ChartManager.initInversionChart('inversionChart', inversionPeriods);
        }

        // 3. 分布图
        const stats = Statistics.calculateBasicStats(data);
        const histogram = Statistics.calculateHistogram(data, 30);
        if (stats && histogram) {
            ChartManager.initDistributionChart('distributionChart', histogram, stats.mean, stats.median);
        }

        // 4. 波动率图
        const rollingStd = Statistics.calculateRollingStd(data, 30);
        if (rollingStd.length > 0) {
            ChartManager.initVolatilityChart('volatilityChart', rollingStd);
        }

        // 5. 对比图
        updateComparisonChart();
    }

    /**
     * 更新对比图表
     */
    function updateComparisonChart() {
        const data = state.currentData;
        if (!data || data.length === 0) return;

        let comparisonData;

        switch (state.comparisonTab) {
            case 'decade':
                comparisonData = Comparison.compareByDecade(data);
                break;
            case 'recession':
                comparisonData = Comparison.compareByRecession(data);
                break;
            case 'seasonality':
                comparisonData = Comparison.analyzeSeasonality(data);
                break;
            default:
                comparisonData = Comparison.compareByDecade(data);
        }

        ChartManager.initComparisonChart('comparisonChart', state.comparisonTab, comparisonData);
    }

    /**
     * 更新统计表格
     */
    function updateStatisticsTables() {
        const data = state.currentData;
        if (!data || data.length === 0) return;

        // 基础统计
        const stats = Statistics.calculateBasicStats(data);
        const basicStatsTable = document.getElementById('basicStats');
        if (basicStatsTable && stats) {
            basicStatsTable.innerHTML = Statistics.formatStatsAsTable(stats);
        }

        // 倒挂统计
        const inversionStats = InversionAnalyzer.calculateInversionStats(data);
        const inversionStatsTable = document.getElementById('inversionStats');
        if (inversionStatsTable) {
            inversionStatsTable.innerHTML = formatInversionStats(inversionStats);
        }

        // 分位数
        const percentiles = Statistics.calculatePercentiles(data, [25, 50, 75, 90, 95]);
        const percentileTable = document.getElementById('percentileStats');
        if (percentileTable) {
            percentileTable.innerHTML = Statistics.formatPercentilesAsTable(percentiles);
        }
    }

    /**
     * 格式化倒挂统计为表格
     */
    function formatInversionStats(stats) {
        let html = '<table><tbody>';
        html += `<tr><td>倒挂天数</td><td>${stats.inversionDays}</td></tr>`;
        html += `<tr><td>正常天数</td><td>${stats.nonInversionDays}</td></tr>`;
        html += `<tr><td>倒挂比例</td><td>${stats.inversionRatio}%</td></tr>`;
        html += `<tr><td>倒挂次数</td><td>${stats.periodsCount}</td></tr>`;
        html += `<tr><td>最长倒挂</td><td>${stats.maxDuration} 天</td></tr>`;
        html += `<tr><td>平均持续</td><td>${stats.avgDuration} 天</td></tr>`;
        if (stats.mostSevere) {
            html += `<tr><td>最严重倒挂</td><td>${stats.mostSevere.value}% (${stats.mostSevere.date})</td></tr>`;
        }
        html += '</tbody></table>';
        return html;
    }

    /**
     * 处理时间范围变化
     */
    function handleTimeRangeChange() {
        updateAll();
    }

    /**
     * 处理数据粒度变化
     */
    function handleGranularityChange() {
        updateAll();
    }

    /**
     * 处理对比标签变化
     */
    function handleComparisonTabChange(tab) {
        state.comparisonTab = tab;

        // 更新标签按钮状态
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.tab === tab) {
                btn.classList.add('active');
            }
        });

        updateComparisonChart();
    }

    /**
     * 导出数据
     */
    function exportData() {
        const data = state.currentData;
        if (!data || data.length === 0) {
            alert('没有数据可导出');
            return;
        }

        // 转换为CSV格式
        let csv = 'DATE,VALUE\n';
        data.forEach(row => {
            csv += `${row.date},${row.value}\n`;
        });

        // 创建下载链接
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', `10y2y_spread_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    /**
     * 显示/隐藏加载状态
     */
    function showLoading(show) {
        state.isLoading = show;
        // 可以添加加载动画
    }

    /**
     * 显示错误消息
     */
    function showError(message) {
        alert(message); // 简单实现，可以替换为更好的UI
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // 暴露到全局作用域（方便调试）
    window.TenYearTwoYearApp = {
        init,
        state,
        updateAll,
        exportData
    };

})();
