/**
 * 美国国债收益率分析 - 主控制器
 * 协调各个模块，处理用户交互
 */

(function() {
    'use strict';

    // 应用状态
    const state = {
        rawData: [],
        currentData: [],
        visibleTenors: ['DGS1', 'DGS2', 'DGS3', 'DGS5', 'DGS10'],
        timeRange: '1y',
        granularity: 'day',
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
            // 使用前向填充处理空值
            state.rawData = DataProcessor.fillMissingValues(state.rawData, 'forward');
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
                ChartManager.resetZoom('mainTrend');
            });
        }

        // 导出按钮
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', exportData);
        }
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
        updateCharts();

        // 更新统计表格
        updateStatisticsTables();
    }

    /**
     * 更新KPI卡片
     */
    function updateKPICards() {
        const data = state.currentData;
        if (!data || data.length === 0) return;

        // 获取各期限当前值
        const currentValues = CurveAnalyzer.getCurrentValues(data, state.visibleTenors);

        // 更新各期限收益率KPI
        state.visibleTenors.forEach(tenor => {
            const elementId = tenor.toLowerCase() + 'Value';
            const value = currentValues[tenor];
            if (value !== null) {
                updateKPI(elementId, value.toFixed(2));
            } else {
                updateKPI(elementId, '--');
            }
        });

        // 更新曲线陡峭度
        const steepness = CurveAnalyzer.getCurrentSteepness(data);
        if (steepness) {
            updateKPI('steepnessValue', steepness.value.toFixed(2));
        } else {
            updateKPI('steepnessValue', '--');
        }

        // 更新数据覆盖天数
        updateKPI('dataDays', data.length.toString());
    }

    /**
     * 更新单个KPI卡片
     */
    function updateKPI(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    /**
     * 更新所有图表
     */
    function updateCharts() {
        const data = state.currentData;
        if (!data || data.length === 0) return;

        // 1. 主趋势图
        ChartManager.initMainTrendChart('mainTrendChart', data, state.visibleTenors);

        // 2. 利差分析图
        ChartManager.initSpreadChart('spreadChart', data, state.visibleTenors);

        // 3. 期限结构图
        const termStructure = CurveAnalyzer.getLatestTermStructure(data, state.visibleTenors);
        if (termStructure) {
            ChartManager.initTermStructureChart('termStructureChart', termStructure, state.visibleTenors);
        }

        // 4. 分布直方图
        const histograms = {};
        state.visibleTenors.forEach(tenor => {
            histograms[tenor] = Statistics.calculateHistogram(data, tenor, 30);
        });
        ChartManager.initDistributionChart('distributionChart', histograms, state.visibleTenors);

        // 5. 波动率分析图
        const rollingStds = Statistics.calculateAllRollingStd(data, state.visibleTenors, 30);
        ChartManager.initVolatilityChart('volatilityChart', rollingStds, state.visibleTenors);
    }

    /**
     * 更新统计表格
     */
    function updateStatisticsTables() {
        const data = state.currentData;
        if (!data || data.length === 0) return;

        // 基础统计
        const allStats = Statistics.calculateAllTenorStats(data, state.visibleTenors);
        const basicStatsTable = document.getElementById('basicStats');
        if (basicStatsTable) {
            basicStatsTable.innerHTML = Statistics.formatStatsAsTable(allStats);
        }

        // 分位数
        const allPercentiles = Statistics.calculateAllTenorPercentiles(data, state.visibleTenors, [25, 50, 75, 90, 95]);
        const percentileTable = document.getElementById('percentileStats');
        if (percentileTable) {
            percentileTable.innerHTML = Statistics.formatPercentilesAsTable(allPercentiles);
        }
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
     * 导出数据
     */
    function exportData() {
        const data = state.currentData;
        if (!data || data.length === 0) {
            alert('没有数据可导出');
            return;
        }

        // 转换为CSV格式
        let csv = 'DATE,' + state.visibleTenors.join(',') + '\n';
        data.forEach(row => {
            const values = state.visibleTenors.map(tenor => {
                const val = row[tenor];
                return val !== null ? val.toFixed(2) : '';
            });
            csv += `${row.date},${values.join(',')}\n`;
        });

        // 创建下载链接
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', `treasury_yield_${new Date().toISOString().split('T')[0]}.csv`);
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
    window.TreasuryYieldApp = {
        init,
        state,
        updateAll,
        exportData
    };

})();
