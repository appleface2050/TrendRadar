/**
 * 图表管理模块
 * 负责所有 Chart.js 图表的初始化和更新
 */

const ChartManager = (function() {
    let charts = {};

    // 期限颜色配置
    const TENOR_COLORS = {
        DGS1: '#3B82F6',
        DGS2: '#10B981',
        DGS3: '#F59E0B',
        DGS5: '#F97316',
        DGS10: '#8B5CF6'
    };

    const TENOR_LABELS = {
        DGS1: '1年期',
        DGS2: '2年期',
        DGS3: '3年期',
        DGS5: '5年期',
        DGS10: '10年期'
    };

    // 默认图表配置
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false,
        },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    color: 'rgba(255, 255, 255, 0.60)'
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(30, 30, 30, 0.95)',
                titleColor: '#FFFFFF',
                bodyColor: 'rgba(255, 255, 255, 0.87)',
                borderColor: 'rgba(124, 58, 237, 0.5)',
                borderWidth: 1
            }
        }
    };

    /**
     * 初始化主趋势图 - 多期限折线图
     * @param {string} canvasId - Canvas元素ID
     * @param {Array} data - 数据数组
     * @param {Array} visibleTenors - 可见期限数组
     * @returns {Chart} Chart实例
     */
    function initMainTrendChart(canvasId, data, visibleTenors = ['DGS1', 'DGS2', 'DGS3', 'DGS5', 'DGS10']) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (charts.mainTrend) {
            charts.mainTrend.destroy();
        }

        const datasets = visibleTenors.map(tenor => ({
            label: TENOR_LABELS[tenor],
            data: data.map(d => d[tenor]),
            borderColor: TENOR_COLORS[tenor],
            backgroundColor: TENOR_COLORS[tenor] + '20',
            borderWidth: 2,
            pointRadius: data.length > 1000 ? 0 : (data.length > 500 ? 1 : 2),
            pointHoverRadius: 5,
            pointBackgroundColor: TENOR_COLORS[tenor],
            pointBorderColor: '#FFFFFF',
            pointBorderWidth: 1,
            fill: false,
            tension: 0.1,
            spanGaps: true,
            tenor: tenor // 自定义属性，用于后续识别
        }));

        const chartConfig = {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: datasets
            },
            options: {
                ...defaultOptions,
                layout: {
                    padding: {
                        left: 10,
                        right: 15,
                        top: 10,
                        bottom: 10
                    }
                },
                plugins: {
                    ...defaultOptions.plugins,
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true,
                                speed: 0.1
                            },
                            pinch: {
                                enabled: true
                            },
                            drag: {
                                enabled: false
                            },
                            mode: 'x'
                        },
                        pan: {
                            enabled: true,
                            mode: 'x',
                            modifierKey: null,
                            threshold: 10,
                            onPanStart: function({chart}) {
                                chart.$testPan = true;
                            },
                            onPanRejected: function({chart}) {
                                delete chart.$testPan;
                            }
                        },
                        limits: {
                            x: { minRange: 10 }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '日期',
                            color: 'rgba(255, 255, 255, 0.60)'
                        },
                        ticks: {
                            maxTicksLimit: 20,
                            maxRotation: 0,
                            autoSkip: true,
                            autoSkipPadding: 20,
                            color: 'rgba(255, 255, 255, 0.60)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.06)'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '收益率 (%)',
                            color: 'rgba(255, 255, 255, 0.60)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.60)',
                            callback: function(value) {
                                return value.toFixed(2) + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.06)'
                        }
                    }
                }
            }
        };

        charts.mainTrend = new Chart(ctx, chartConfig);
        return charts.mainTrend;
    }

    /**
     * 初始化利差分析图
     * @param {string} canvasId - Canvas元素ID
     * @param {Array} data - 数据数组
     * @param {Array} visibleTenors - 可见期限数组
     * @returns {Chart} Chart实例
     */
    function initSpreadChart(canvasId, data, visibleTenors) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (charts.spread) {
            charts.spread.destroy();
        }

        // 计算各期限与10Y的利差
        const spreads = {};
        visibleTenors.filter(t => t !== 'DGS10').forEach(tenor => {
            spreads[tenor] = data.map(row => {
                const v10y = row.DGS10;
                const vTenor = row[tenor];
                if (v10y !== null && vTenor !== null) {
                    return vTenor - v10y;
                }
                return null;
            });
        });

        const datasets = Object.keys(spreads).map(tenor => ({
            label: TENOR_LABELS[tenor] + '-10Y',
            data: spreads[tenor],
            borderColor: TENOR_COLORS[tenor],
            backgroundColor: TENOR_COLORS[tenor] + '20',
            borderWidth: 2,
            pointRadius: data.length > 500 ? 0 : 1,
            pointHoverRadius: 4,
            fill: false,
            tension: 0.1,
            spanGaps: true,
            tenor: tenor
        }));

        const chartConfig = {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: datasets
            },
            options: {
                ...defaultOptions,
                plugins: {
                    ...defaultOptions.plugins,
                    annotation: {
                        annotations: {
                            zeroLine: {
                                type: 'line',
                                yMin: 0,
                                yMax: 0,
                                borderColor: '#666',
                                borderWidth: 2,
                                borderDash: [5, 5]
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '日期',
                            color: '#6B7280'
                        },
                        ticks: {
                            maxTicksLimit: 15,
                            color: '#9CA3AF'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '利差 (%)',
                            color: '#6B7280'
                        },
                        ticks: {
                            color: '#9CA3AF',
                            callback: function(value) {
                                return value.toFixed(2) + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)'
                        }
                    }
                }
            }
        };

        charts.spread = new Chart(ctx, chartConfig);
        return charts.spread;
    }

    /**
     * 初始化期限结构图
     * @param {string} canvasId - Canvas元素ID
     * @param {Object} termStructure - 期限结构数据
     * @param {Array} visibleTenors - 可见期限数组
     * @returns {Chart} Chart实例
     */
    function initTermStructureChart(canvasId, termStructure, visibleTenors) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || !termStructure) return null;

        if (charts.termStructure) {
            charts.termStructure.destroy();
        }

        const labels = [];
        const data = [];

        visibleTenors.forEach(tenor => {
            labels.push(TENOR_LABELS[tenor]);
            data.push(termStructure[tenor]);
        });

        const chartConfig = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '收益率',
                    data: data,
                    backgroundColor: visibleTenors.map(t => TENOR_COLORS[t] + 'CC'),
                    borderColor: visibleTenors.map(t => TENOR_COLORS[t]),
                    borderWidth: 2,
                    borderRadius: 6
                }]
            },
            options: {
                ...defaultOptions,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '期限',
                            color: '#6B7280'
                        },
                        ticks: {
                            color: '#9CA3AF'
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: '收益率 (%)',
                            color: '#6B7280'
                        },
                        ticks: {
                            color: '#9CA3AF',
                            callback: function(value) {
                                return value.toFixed(2) + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)'
                        }
                    }
                }
            }
        };

        charts.termStructure = new Chart(ctx, chartConfig);
        return charts.termStructure;
    }

    /**
     * 初始化分布直方图
     * @param {string} canvasId - Canvas元素ID
     * @param {Object} histograms - 各期限直方图数据
     * @param {Array} visibleTenors - 可见期限数组
     * @returns {Chart} Chart实例
     */
    function initDistributionChart(canvasId, histograms, visibleTenors) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || !histograms) return null;

        if (charts.distribution) {
            charts.distribution.destroy();
        }

        // 使用第一个期限的标签作为x轴
        const firstTenor = visibleTenors[0];
        const labels = histograms[firstTenor]?.labels || [];

        const datasets = visibleTenors.map(tenor => {
            const hist = histograms[tenor];
            return {
                label: TENOR_LABELS[tenor],
                data: hist?.data || [],
                backgroundColor: TENOR_COLORS[tenor] + '80',
                borderColor: TENOR_COLORS[tenor],
                borderWidth: 1,
                borderRadius: 4,
                tenor: tenor
            };
        });

        const chartConfig = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                ...defaultOptions,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '收益率 (%)',
                            color: '#6B7280'
                        },
                        ticks: {
                            color: '#9CA3AF',
                            maxTicksLimit: 15
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '频数',
                            color: '#6B7280'
                        },
                        ticks: {
                            color: '#9CA3AF'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)'
                        }
                    }
                }
            }
        };

        charts.distribution = new Chart(ctx, chartConfig);
        return charts.distribution;
    }

    /**
     * 初始化波动率分析图
     * @param {string} canvasId - Canvas元素ID
     * @param {Object} rollingStds - 各期限滚动标准差
     * @param {Array} visibleTenors - 可见期限数组
     * @returns {Chart} Chart实例
     */
    function initVolatilityChart(canvasId, rollingStds, visibleTenors) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || !rollingStds) return null;

        if (charts.volatility) {
            charts.volatility.destroy();
        }

        // 使用第一个期限的日期作为x轴
        const firstTenor = visibleTenors[0];
        const labels = rollingStds[firstTenor]?.map(d => d.date) || [];

        const datasets = visibleTenors.map(tenor => {
            const stdData = rollingStds[tenor] || [];
            return {
                label: TENOR_LABELS[tenor],
                data: stdData.map(d => d.value),
                borderColor: TENOR_COLORS[tenor],
                backgroundColor: TENOR_COLORS[tenor] + '20',
                borderWidth: 2,
                pointRadius: 1,
                pointHoverRadius: 4,
                fill: false,
                tension: 0.4,
                tenor: tenor
            };
        });

        const chartConfig = {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                ...defaultOptions,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '日期',
                            color: '#6B7280'
                        },
                        ticks: {
                            maxTicksLimit: 15,
                            color: '#9CA3AF'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '标准差 (%)',
                            color: '#6B7280'
                        },
                        ticks: {
                            color: '#9CA3AF',
                            callback: function(value) {
                                return value.toFixed(2) + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)'
                        }
                    }
                }
            }
        };

        charts.volatility = new Chart(ctx, chartConfig);
        return charts.volatility;
    }

    /**
     * 更新图表数据集可见性
     * @param {string} chartName - 图表名称
     * @param {Array} visibleTenors - 可见期限数组
     */
    function updateDatasetVisibility(chartName, visibleTenors) {
        const chart = charts[chartName];
        if (!chart) return;

        chart.data.datasets.forEach(dataset => {
            const tenor = dataset.tenor;
            if (tenor) {
                dataset.hidden = !visibleTenors.includes(tenor);
            }
        });

        chart.update();
    }

    /**
     * 重置图表缩放
     * @param {string} chartName - 图表名称
     */
    function resetZoom(chartName) {
        if (charts[chartName] && charts[chartName].resetZoom) {
            charts[chartName].resetZoom();
        }
    }

    /**
     * 销毁指定图表
     * @param {string} chartName - 图表名称
     */
    function destroyChart(chartName) {
        if (charts[chartName]) {
            charts[chartName].destroy();
            delete charts[chartName];
        }
    }

    /**
     * 销毁所有图表
     */
    function destroyAllCharts() {
        Object.keys(charts).forEach(key => {
            if (charts[key]) {
                charts[key].destroy();
            }
        });
        charts = {};
    }

    /**
     * 获取图表实例
     * @param {string} chartName - 图表名称
     * @returns {Chart} Chart实例
     */
    function getChart(chartName) {
        return charts[chartName];
    }

    // 公共 API
    return {
        initMainTrendChart,
        initSpreadChart,
        initTermStructureChart,
        initDistributionChart,
        initVolatilityChart,
        updateDatasetVisibility,
        resetZoom,
        destroyChart,
        destroyAllCharts,
        getChart,
        get TENOR_COLORS() { return TENOR_COLORS; },
        get TENOR_LABELS() { return TENOR_LABELS; },
        get charts() { return charts; }
    };
})();
