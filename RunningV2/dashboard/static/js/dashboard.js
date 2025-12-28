/**
 * RunningV2 Dashboard - 前端逻辑
 * Clean White Sport Edition
 * 使用 Chart.js 渲染 RQ 预测图表,配合数字滚动动画
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
        showError('网络错误,请稍后重试');
    }
}

/**
 * 渲染图表 - 清新白色风格
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

    // 创建新图表 - 清新白色风格
    rqChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: '历史数据',
                    data: historyData,
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: '#3b82f6',
                    pointRadius: 2.5,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#3b82f6',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2,
                    order: 2
                },
                {
                    label: '预测值',
                    data: forecastData,
                    backgroundColor: 'rgba(16, 185, 129, 0.9)',
                    borderColor: '#10b981',
                    pointRadius: 4,
                    pointHoverRadius: 8,
                    pointHoverBackgroundColor: '#10b981',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2,
                    order: 1
                },
                {
                    label: '预测区间上界',
                    data: forecastData.map(d => ({ x: d.x, y: d.yhat_upper })),
                    type: 'line',
                    borderColor: 'rgba(16, 185, 129, 0.3)',
                    backgroundColor: 'transparent',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                    order: 0
                },
                {
                    label: '预测区间下界',
                    data: forecastData.map(d => ({ x: d.x, y: d.yhat_lower })),
                    type: 'line',
                    borderColor: 'rgba(16, 185, 129, 0.3)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: '-1', // 填充到上一个数据集(上界)
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
                    text: '能力值预测趋势(未来30天)',
                    font: {
                        family: "'Poppins', sans-serif",
                        size: 18,
                        weight: '600'
                    },
                    color: '#1e293b',
                    padding: {
                        top: 10,
                        bottom: 25
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(255, 255, 255, 0.98)',
                    titleColor: '#1e293b',
                    bodyColor: '#64748b',
                    borderColor: '#e2e8f0',
                    borderWidth: 1,
                    padding: 14,
                    titleFont: {
                        family: "'Poppins', sans-serif",
                        size: 14,
                        weight: '600'
                    },
                    bodyFont: {
                        family: "'Inter', sans-serif",
                        size: 13
                    },
                    displayColors: true,
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
                            family: "'Poppins', sans-serif",
                            size: 13,
                            weight: '500'
                        },
                        color: '#64748b'
                    },
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11
                        },
                        color: '#64748b',
                        maxRotation: 45,
                        minRotation: 45,
                        maxTicksLimit: 12
                    },
                    grid: {
                        color: '#f1f5f9',
                        borderColor: '#e2e8f0'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '能力值',
                        font: {
                            family: "'Poppins', sans-serif",
                            size: 13,
                            weight: '500'
                        },
                        color: '#64748b'
                    },
                    ticks: {
                        font: {
                            family: "'Inter', sans-serif",
                            size: 11
                        },
                        color: '#64748b'
                    },
                    grid: {
                        color: '#f1f5f9',
                        borderColor: '#e2e8f0'
                    },
                    beginAtZero: false
                }
            },
            animation: {
                duration: 1200,
                easing: 'easeOutCubic'
            }
        }
    });
}

/**
 * 更新统计信息 - 带数字滚动动画
 */
function updateStats(forecastData, statsData) {
    // 当前 RQ
    const currentRQ = parseFloat(forecastData.history[forecastData.history.length - 1].rq);
    animateValue('current-rq', currentRQ, 1);

    // 30天预测增长
    const lastForecast = forecastData.forecast[forecastData.forecast.length - 1];
    const growth = lastForecast.yhat - currentRQ;
    const growthElement = document.getElementById('forecast-growth');

    // 延迟执行增长动画,让当前 RQ 先完成动画
    setTimeout(() => {
        animateValue('forecast-growth', growth, 1, true);

        // 根据正负值设置颜色
        setTimeout(() => {
            growthElement.style.color = growth > 0 ? '#10b981' : (growth < 0 ? '#ef4444' : '#3b82f6');
        }, 600);
    }, 400);

    // 历史最大值和最小值
    if (statsData.success) {
        setTimeout(() => {
            animateValue('max-rq', statsData.max, 1);
        }, 200);

        setTimeout(() => {
            animateValue('min-rq', statsData.min, 1);
        }, 600);
    } else {
        // 从历史数据计算
        const allValues = forecastData.history.map(d => parseFloat(d.rq));
        setTimeout(() => {
            animateValue('max-rq', Math.max(...allValues), 1);
        }, 200);

        setTimeout(() => {
            animateValue('min-rq', Math.min(...allValues), 1);
        }, 600);
    }

    hideLoading();
}

/**
 * 数字滚动动画
 * @param {string} elementId - 元素 ID
 * @param {number} endValue - 结束值
 * @param {number} decimals - 小数位数
 * @param {boolean} showSign - 是否显示正负号
 * @param {number} duration - 动画持续时间(毫秒)
 */
function animateValue(elementId, endValue, decimals = 0, showSign = false, duration = 700) {
    const element = document.getElementById(elementId);
    const startValue = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // 使用 easeOutCubic 缓动函数
        const easeProgress = 1 - Math.pow(1 - progress, 3);

        const currentValue = startValue + (endValue - startValue) * easeProgress;

        // 格式化数值
        let formatted = currentValue.toFixed(decimals);
        if (showSign && currentValue > 0) {
            formatted = '+' + formatted;
        }

        element.textContent = formatted;
        element.style.opacity = progress;

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            // 动画完成,确保最终值精确
            let finalFormatted = endValue.toFixed(decimals);
            if (showSign && endValue > 0) {
                finalFormatted = '+' + finalFormatted;
            }
            element.textContent = finalFormatted;
        }
    }

    requestAnimationFrame(update);
}

/**
 * 显示加载状态
 */
function showLoading() {
    const chartCanvas = document.getElementById('rq-chart');
    if (chartCanvas) {
        chartCanvas.style.opacity = '0.4';
    }

    // 更新统计卡片为加载状态
    const elements = ['current-rq', 'forecast-growth', 'max-rq', 'min-rq'];
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = '---';
            element.style.opacity = '0.5';
        }
    });
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    const chartCanvas = document.getElementById('rq-chart');
    if (chartCanvas) {
        chartCanvas.style.opacity = '1';
        // 添加淡入动画
        chartCanvas.style.transition = 'opacity 0.4s ease';
    }
}

/**
 * 显示错误信息 - 使用自定义提示而非 alert
 */
function showError(message) {
    // 创建错误提示元素
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-toast';
    errorDiv.innerHTML = `
        <div class="error-icon">⚠️</div>
        <div class="error-message">${message}</div>
    `;

    // 添加样式
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        color: #1e293b;
        padding: 18px 22px;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 12px;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        animation: slideInRight 0.4s ease-out;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #ef4444;
    `;

    // 添加动画关键帧
    if (!document.getElementById('error-toast-style')) {
        const style = document.createElement('style');
        style.id = 'error-toast-style';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    opacity: 0;
                    transform: translateX(50px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            @keyframes slideOutRight {
                from {
                    opacity: 1;
                    transform: translateX(0);
                }
                to {
                    opacity: 0;
                    transform: translateX(50px);
                }
            }
            .error-icon {
                font-size: 1.3rem;
                animation: shake 0.4s ease-in-out;
            }
            @keyframes shake {
                0%, 100% { transform: rotate(0deg); }
                25% { transform: rotate(-8deg); }
                75% { transform: rotate(8deg); }
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(errorDiv);

    // 5秒后自动移除
    setTimeout(() => {
        errorDiv.style.animation = 'slideOutRight 0.4s ease-out';
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 400);
    }, 5000);

    hideLoading();
}

// 窗口大小改变时重新渲染图表
window.addEventListener('resize', function() {
    if (rqChart) {
        rqChart.resize();
    }
});

/**
 * 添加键盘快捷键支持
 */
document.addEventListener('keydown', function(event) {
    // 按 R 键刷新数据
    if (event.key === 'r' || event.key === 'R') {
        if (!event.ctrlKey && !event.metaKey) {
            loadData();
        }
    }
});

/**
 * 页面可见性变化时自动刷新
 */
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        // 页面重新可见时,如果数据超过5分钟,自动刷新
        const lastRefresh = sessionStorage.getItem('lastRefresh');
        const now = Date.now();

        if (!lastRefresh || (now - parseInt(lastRefresh)) > 5 * 60 * 1000) {
            loadData();
            sessionStorage.setItem('lastRefresh', now.toString());
        }
    }
});

// 记录首次刷新时间
sessionStorage.setItem('lastRefresh', Date.now().toString());
