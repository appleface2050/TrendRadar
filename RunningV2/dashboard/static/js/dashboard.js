/**
 * RunningV2 Dashboard - 前端逻辑
 * 使用 Chart.js 渲染 RQ 预测图表
 */

let rqChart = null;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadData();
});

/**
 * 从 API 加载数据
 */
async function loadData() {
    showLoading();

    try {
        // 并行获取预测数据和统计数据
        const [forecastResponse, statsResponse] = await Promise.all([
            fetch('/api/rq/forecast'),
            fetch('/api/rq/stats')
        ]);

        const forecastData = await forecastResponse.json();
        const statsData = await statsResponse.json();

        if (forecastData.success) {
            renderChart(forecastData);
            updateStats(forecastData, statsData);
        } else {
            showError('加载数据失败: ' + forecastData.error);
        }

    } catch (error) {
        console.error('加载数据失败:', error);
        showError('网络错误，请稍后重试');
    }
}

/**
 * 渲染图表
 */
function renderChart(data) {
    const ctx = document.getElementById('rq-chart').getContext('2d');

    // 准备历史数据
    const historyData = data.history.map(item => ({
        x: item.date,
        y: parseFloat(item.rq)
    }));

    // 准备预测数据
    const forecastData = data.forecast.map(item => ({
        x: item.ds,
        y: item.yhat,
        yhat_lower: item.yhat_lower,
        yhat_upper: item.yhat_upper
    }));

    // 销毁旧图表
    if (rqChart) {
        rqChart.destroy();
    }

    // 创建新图表
    rqChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: '历史数据',
                    data: historyData,
                    backgroundColor: '#5470c6',
                    borderColor: '#5470c6',
                    pointRadius: 1.5,
                    pointHoverRadius: 4,
                    order: 2
                },
                {
                    label: '预测值',
                    data: forecastData,
                    backgroundColor: '#91cc75',
                    borderColor: '#91cc75',
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    order: 1
                },
                {
                    label: '预测区间上界',
                    data: forecastData.map(d => ({ x: d.x, y: d.yhat_upper })),
                    type: 'line',
                    borderColor: 'rgba(145, 204, 117, 0.2)',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false,
                    order: 0
                },
                {
                    label: '预测区间下界',
                    data: forecastData.map(d => ({ x: d.x, y: d.yhat_lower })),
                    type: 'line',
                    borderColor: 'rgba(145, 204, 117, 0.2)',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: '-1', // 填充到上一个数据集（上界）
                    backgroundColor: 'rgba(145, 204, 117, 0.1)',
                    order: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    left: 10,
                    right: 20,
                    top: 10,
                    bottom: 10
                }
            },
            interaction: {
                intersect: false,
                mode: 'nearest'
            },
            plugins: {
                title: {
                    display: true,
                    text: 'RQ 能力值预测（未来30天）',
                    font: {
                        size: 18,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        title: function(context) {
                            const date = new Date(context[0].parsed.x);
                            return date.toLocaleDateString('zh-CN');
                        },
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y.toFixed(2);
                            return label;
                        }
                    }
                },
                legend: {
                    display: false // 使用自定义图例
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'month',
                        displayFormats: {
                            month: 'yyyy-MM'
                        }
                    },
                    title: {
                        display: true,
                        text: '日期',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        maxTicksLimit: 12
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'RQ 值',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    beginAtZero: false
                }
            }
        }
    });
}

/**
 * 更新统计信息
 */
function updateStats(forecastData, statsData) {
    // 当前 RQ
    const currentRQ = forecastData.history[forecastData.history.length - 1].rq;
    document.getElementById('current-rq').textContent = parseFloat(currentRQ).toFixed(1);

    // 30天预测增长
    const lastForecast = forecastData.forecast[forecastData.forecast.length - 1];
    const growth = lastForecast.yhat - parseFloat(currentRQ);
    const growthElement = document.getElementById('forecast-growth');
    growthElement.textContent = (growth > 0 ? '+' : '') + growth.toFixed(1);
    growthElement.style.color = growth > 0 ? '#67c23a' : (growth < 0 ? '#f56c6c' : '#409eff');

    // 历史最大值和最小值
    if (statsData.success) {
        document.getElementById('max-rq').textContent = statsData.max.toFixed(1);
        document.getElementById('min-rq').textContent = statsData.min.toFixed(1);
    } else {
        // 从历史数据计算
        const allValues = forecastData.history.map(d => parseFloat(d.rq));
        document.getElementById('max-rq').textContent = Math.max(...allValues).toFixed(1);
        document.getElementById('min-rq').textContent = Math.min(...allValues).toFixed(1);
    }

    hideLoading();
}

/**
 * 显示加载状态
 */
function showLoading() {
    const chartCanvas = document.getElementById('rq-chart');
    chartCanvas.style.opacity = '0.5';

    // 更新统计卡片为加载状态
    document.getElementById('current-rq').textContent = '加载中...';
    document.getElementById('forecast-growth').textContent = '-';
    document.getElementById('max-rq').textContent = '-';
    document.getElementById('min-rq').textContent = '-';
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    const chartCanvas = document.getElementById('rq-chart');
    chartCanvas.style.opacity = '1';
}

/**
 * 显示错误信息
 */
function showError(message) {
    alert('错误: ' + message);
    hideLoading();
}

// 窗口大小改变时重新渲染图表
window.addEventListener('resize', function() {
    if (rqChart) {
        rqChart.resize();
    }
});
