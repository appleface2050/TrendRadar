/**
 * 图表管理模块
 * 负责所有 Chart.js 图表的初始化和更新
 */

const ChartManager = (function() {
    let charts = {};

    // 默认图表配置
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    color: '#6B7280'
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(30, 30, 47, 0.95)',
                titleColor: '#FFFFFF',
                bodyColor: '#E0E0E0',
                borderColor: 'rgba(108, 92, 231, 0.5)',
                borderWidth: 1
            }
        }
    };

    /**
     * 初始化长期趋势图表
     * @param {string} canvasId - Canvas元素ID
     * @param {Array} data - 数据数组
     * @param {Array} annotations - 标注数组（可选）
     * @returns {Chart} Chart实例
     */
    function initTrendChart(canvasId, data, annotations = null) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        // 销毁旧图表
        if (charts.trend) {
            charts.trend.destroy();
        }

        // 创建渐变
        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(108, 92, 231, 0.4)');
        gradient.addColorStop(0.5, 'rgba(108, 92, 231, 0.2)');
        gradient.addColorStop(1, 'rgba(108, 92, 231, 0.0)');

        // 根据正负值设置颜色（绿色正值，橙色负值）
        const colors = data.map(d => d.value >= 0 ? '#4CAF50' : '#FFA500');

        const chartConfig = {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: '10y-2y 利差 (%)',
                    data: data.map(d => d.value),
                    borderColor: '#6C5CE7',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    pointRadius: data.length > 500 ? 0 : 2,
                    pointHoverRadius: 5,
                    pointBackgroundColor: '#6C5CE7',
                    pointBorderColor: '#FFFFFF',
                    pointBorderWidth: 2,
                    fill: true,
                    tension: 0.1
                }]
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
                    annotation: {
                        annotations: {
                            zeroLine: {
                                type: 'line',
                                yMin: 0,
                                yMax: 0,
                                borderColor: '#666',
                                borderWidth: 2,
                                borderDash: [5, 5],
                                label: {
                                    display: false,
                                    content: '零线（倒挂分界）',
                                    position: 'end'
                                }
                            },
                            ...(annotations || {})
                        }
                    },
                    zoom: {
                        zoom: {
                            wheel: { enabled: true },
                            pinch: { enabled: true },
                            mode: 'x'
                        },
                        pan: {
                            enabled: true,
                            mode: 'x'
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '日期',
                            color: '#6B7280'
                        },
                        ticks: {
                            maxTicksLimit: 20,
                            maxRotation: 0,
                            autoSkip: true,
                            autoSkipPadding: 20,
                            color: '#9CA3AF'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: '利差 (%)',
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

        charts.trend = new Chart(ctx, chartConfig);
        return charts.trend;
    }

    /**
     * 更新趋势图表
     * @param {Array} data - 新数据
     * @param {Array} annotations - 标注数组（可选）
     */
    function updateTrendChart(data, annotations = null) {
        if (!charts.trend) return;

        charts.trend.data.labels = data.map(d => d.date);
        charts.trend.data.datasets[0].data = data.map(d => d.value);

        if (annotations) {
            charts.trend.options.plugins.annotation.annotations = {
                zeroLine: charts.trend.options.plugins.annotation.annotations.zeroLine,
                ...annotations
            };
        }

        charts.trend.update();
    }

    /**
     * 初始化倒挂分析图表
     * @param {string} canvasId - Canvas元素ID
     * @param {Array} periods - 倒挂期数组
     * @returns {Chart} Chart实例
     */
    function initInversionChart(canvasId, periods) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (charts.inversion) {
            charts.inversion.destroy();
        }

        const labels = periods.map((p, i) => `倒挂${i + 1}`);
        const data = periods.map(p => p.days);

        const chartConfig = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '持续天数',
                    data: data,
                    backgroundColor: 'rgba(255, 165, 0, 0.7)',
                    borderColor: 'rgba(255, 165, 0, 1)',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                ...defaultOptions,
                plugins: {
                    ...defaultOptions.plugins,
                    tooltip: {
                        callbacks: {
                            afterBody: function(context) {
                                const index = context[0].dataIndex;
                                const period = periods[index];
                                return [
                                    `开始: ${period.startDate}`,
                                    `结束: ${period.endDate}`,
                                    `最低值: ${period.minValue}%`,
                                    `最低日期: ${period.minDate}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '天数',
                            color: '#6B7280'
                        },
                        ticks: {
                            color: '#9CA3AF'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#9CA3AF'
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        };

        charts.inversion = new Chart(ctx, chartConfig);
        return charts.inversion;
    }

    /**
     * 初始化分布直方图
     * @param {string} canvasId - Canvas元素ID
     * @param {Object} histogram - 直方图数据
     * @param {number} mean - 均值
     * @param {number} median - 中位数
     * @returns {Chart} Chart实例
     */
    function initDistributionChart(canvasId, histogram, mean, median) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (charts.distribution) {
            charts.distribution.destroy();
        }

        const chartConfig = {
            type: 'bar',
            data: {
                labels: histogram.labels,
                datasets: [{
                    label: '频数',
                    data: histogram.data,
                    backgroundColor: 'rgba(108, 92, 231, 0.7)',
                    borderColor: 'rgba(108, 92, 231, 1)',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                ...defaultOptions,
                plugins: {
                    ...defaultOptions.plugins,
                    annotation: {
                        annotations: {
                            meanLine: {
                                type: 'line',
                                xMin: mean,
                                xMax: mean,
                                borderColor: 'rgba(76, 175, 80, 0.8)',
                                borderWidth: 2,
                                label: {
                                    display: true,
                                    content: `均值: ${mean.toFixed(2)}`,
                                    position: 'start'
                                }
                            },
                            medianLine: {
                                type: 'line',
                                xMin: median,
                                xMax: median,
                                borderColor: 'rgba(108, 92, 231, 0.8)',
                                borderWidth: 2,
                                borderDash: [5, 5],
                                label: {
                                    display: true,
                                    content: `中位数: ${median.toFixed(2)}`,
                                    position: 'end'
                                }
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '利差 (%)',
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
     * 初始化波动率图表
     * @param {string} canvasId - Canvas元素ID
     * @param {Array} rollingStd - 滚动标准差数据
     * @returns {Chart} Chart实例
     */
    function initVolatilityChart(canvasId, rollingStd) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (charts.volatility) {
            charts.volatility.destroy();
        }

        const chartConfig = {
            type: 'line',
            data: {
                labels: rollingStd.map(d => d.date),
                datasets: [{
                    label: '30日滚动标准差',
                    data: rollingStd.map(d => d.value),
                    borderColor: 'rgba(108, 92, 231, 1)',
                    backgroundColor: 'rgba(108, 92, 231, 0.2)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: rollingStd.length > 500 ? 0 : 2,
                    pointBackgroundColor: '#6C5CE7',
                    pointBorderColor: '#FFFFFF',
                    pointBorderWidth: 2
                }]
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
                            maxTicksLimit: 20,
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
                            color: '#9CA3AF'
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
     * 初始化对比图表
     * @param {string} canvasId - Canvas元素ID
     * @param {string} type - 对比类型 ('decade', 'recession', 'seasonality')
     * @param {Object} comparisonData - 对比数据
     * @returns {Chart} Chart实例
     */
    function initComparisonChart(canvasId, type, comparisonData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (charts.comparison) {
            charts.comparison.destroy();
        }

        let chartConfig;

        if (type === 'decade') {
            chartConfig = {
                type: 'bar',
                data: {
                    labels: comparisonData.labels,
                    datasets: [
                        {
                            label: '平均利差 (%)',
                            data: comparisonData.avgSpread,
                            backgroundColor: 'rgba(108, 92, 231, 0.7)',
                            borderColor: 'rgba(108, 92, 231, 1)',
                            borderWidth: 1,
                            borderRadius: 6,
                            yAxisID: 'y'
                        },
                        {
                            label: '倒挂比例 (%)',
                            data: comparisonData.inversionRatio,
                            type: 'line',
                            borderColor: 'rgba(255, 165, 0, 1)',
                            backgroundColor: 'rgba(255, 165, 0, 0.2)',
                            borderWidth: 2,
                            pointBackgroundColor: '#FFA500',
                            pointBorderColor: '#FFFFFF',
                            pointBorderWidth: 2,
                            yAxisID: 'y1',
                            tension: 0.1
                        }
                    ]
                },
                options: {
                    ...defaultOptions,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: '平均利差 (%)',
                                color: '#6B7280'
                            },
                            ticks: {
                                color: '#9CA3AF'
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.06)'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: '倒挂比例 (%)',
                                color: '#6B7280'
                            },
                            ticks: {
                                color: '#9CA3AF'
                            },
                            grid: {
                                drawOnChartArea: false
                            },
                            max: 100,
                            min: 0
                        },
                        x: {
                            ticks: {
                                color: '#9CA3AF'
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            };
        } else if (type === 'recession') {
            chartConfig = {
                type: 'line',
                data: {
                    labels: comparisonData.labels,
                    datasets: [
                        {
                            label: '前6月均值',
                            data: comparisonData.preAvg,
                            borderColor: 'rgba(76, 175, 80, 1)',
                            backgroundColor: 'rgba(76, 175, 80, 0.2)',
                            borderWidth: 2,
                            pointBackgroundColor: '#4CAF50',
                            pointBorderColor: '#FFFFFF',
                            pointBorderWidth: 2
                        },
                        {
                            label: '期间均值',
                            data: comparisonData.duringAvg,
                            borderColor: 'rgba(255, 165, 0, 1)',
                            backgroundColor: 'rgba(255, 165, 0, 0.2)',
                            borderWidth: 2,
                            pointBackgroundColor: '#FFA500',
                            pointBorderColor: '#FFFFFF',
                            pointBorderWidth: 2
                        },
                        {
                            label: '后6月均值',
                            data: comparisonData.postAvg,
                            borderColor: 'rgba(108, 92, 231, 1)',
                            backgroundColor: 'rgba(108, 92, 231, 0.2)',
                            borderWidth: 2,
                            pointBackgroundColor: '#6C5CE7',
                            pointBorderColor: '#FFFFFF',
                            pointBorderWidth: 2
                        }
                    ]
                },
                options: {
                    ...defaultOptions,
                    scales: {
                        x: {
                            ticks: {
                                color: '#9CA3AF'
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.06)'
                            }
                        },
                        y: {
                            ticks: {
                                color: '#9CA3AF'
                            },
                            title: {
                                display: true,
                                text: '利差 (%)',
                                color: '#6B7280'
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.06)'
                            }
                        }
                    }
                }
            };
        } else if (type === 'seasonality') {
            chartConfig = {
                type: 'bar',
                data: {
                    labels: comparisonData.labels,
                    datasets: [{
                        label: '平均利差 (%)',
                        data: comparisonData.avgSpread,
                        backgroundColor: 'rgba(108, 92, 231, 0.7)',
                        borderColor: 'rgba(108, 92, 231, 1)',
                        borderWidth: 1,
                        borderRadius: 6
                    }]
                },
                options: {
                    ...defaultOptions,
                    scales: {
                        y: {
                            title: {
                                display: true,
                                text: '平均利差 (%)',
                                color: '#6B7280'
                            },
                            ticks: {
                                color: '#9CA3AF'
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.06)'
                            }
                        },
                        x: {
                            ticks: {
                                color: '#9CA3AF'
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            };
        }

        charts.comparison = new Chart(ctx, chartConfig);
        return charts.comparison;
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
        initTrendChart,
        updateTrendChart,
        initInversionChart,
        initDistributionChart,
        initVolatilityChart,
        initComparisonChart,
        resetZoom,
        destroyChart,
        destroyAllCharts,
        getChart,
        get charts() { return charts; }
    };
})();
