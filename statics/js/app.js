const macroeconomicData = {
    indicators: {
        gdp: {
            name: 'GDP增长率',
            unit: '%',
            format: (v) => v.toFixed(2),
            annualTarget: 5.0,
            range: { min: 3, max: 8 },
            data: []
        },
        cpi: {
            name: 'CPI通胀率',
            unit: '%',
            format: (v) => v.toFixed(2),
            annualTarget: 3.0,
            range: { min: 0, max: 5 },
            data: []
        },
        unemployment: {
            name: '失业率',
            unit: '%',
            format: (v) => v.toFixed(1),
            annualTarget: 5.5,
            range: { min: 3, max: 7 },
            data: []
        },
        interest: {
            name: '利率',
            unit: '%',
            format: (v) => v.toFixed(2),
            annualTarget: 3.5,
            range: { min: 1.5, max: 6 },
            data: []
        },
        m2: {
            name: 'M2货币供应',
            unit: '万亿元',
            format: (v) => v.toFixed(1),
            annualTarget: 280,
            range: { min: 220, max: 300 },
            data: []
        },
        pmi: {
            name: 'PMI指数',
            unit: '',
            format: (v) => v.toFixed(1),
            annualTarget: 50.5,
            range: { min: 48, max: 55 },
            data: []
        },
        trade: {
            name: '贸易差额',
            unit: '亿美元',
            format: (v) => Math.abs(v).toFixed(1),
            annualTarget: 500,
            range: { min: -200, max: 1000 },
            data: []
        },
        housing: {
            name: '房价指数',
            unit: '',
            format: (v) => v.toFixed(1),
            annualTarget: 105,
            range: { min: 95, max: 110 },
            data: []
        }
    },
    regions: {
        china: { name: '中国' },
        usa: { name: '美国' },
        europe: { name: '欧元区' },
        global: { name: '全球' }
    }
};

let currentIndicator = 'gdp';
let currentRegion = 'china';
let currentTimeRange = '1y';
let charts = {};

function generateMockData(indicator, range, months = 12) {
    const data = [];
    const baseValue = (range.min + range.max) / 2;
    const volatility = (range.max - range.min) * 0.15;

    let currentValue = baseValue + (Math.random() - 0.5) * volatility;

    for (let i = months - 1; i >= 0; i--) {
        const date = new Date();
        date.setMonth(date.getMonth() - i);

        currentValue += (Math.random() - 0.5) * volatility;
        currentValue = Math.max(range.min, Math.min(range.max, currentValue));

        const prevValue = i < months - 1 ? data[data.length - 1].value : currentValue;
        const momChange = ((currentValue - prevValue) / prevValue) * 100;

        const yearAgoValue = baseValue + (Math.random() - 0.5) * volatility * 2;
        const yoyChange = ((currentValue - yearAgoValue) / Math.abs(yearAgoValue)) * 100;

        data.push({
            date: date.toISOString().slice(0, 7),
            value: currentValue,
            mom: momChange,
            yoy: yoyChange,
            percentile: Math.random()
        });
    }

    return data;
}

function initializeData() {
    Object.keys(macroeconomicData.indicators).forEach(key => {
        const indicator = macroeconomicData.indicators[key];
        indicator.data = generateMockData(key, indicator.range, 12);
    });
    updateLastUpdateTime();
}

function getFilteredData(indicator, timeRange) {
    const monthsMap = {
        '1m': 1,
        '3m': 3,
        '6m': 6,
        '1y': 12,
        '5y': 60
    };

    const currentIndicator = indicator || window.currentIndicator || 'gdp';
    const currentTimeRange = timeRange || window.currentTimeRange || '1y';
    const months = monthsMap[currentTimeRange] || 12;

    if (!macroeconomicData.indicators[currentIndicator]) {
        console.warn(`Indicator "${currentIndicator}" not found`);
        return [];
    }

    const allData = macroeconomicData.indicators[currentIndicator].data;
    return allData.slice(-months);
}

function updateKPICards() {
    const indicator = macroeconomicData.indicators[currentIndicator];
    const data = getFilteredData(currentIndicator, currentTimeRange);
    const latestData = data[data.length - 1];
    const previousData = data[data.length - 2] || latestData;

    document.getElementById('currentValue').textContent =
        indicator.format(latestData.value) + indicator.unit;

    const monthChange = latestData.mom;
    const monthChangeEl = document.getElementById('monthChange');
    monthChangeEl.textContent = (monthChange >= 0 ? '+' : '') + monthChange.toFixed(2) + '%';
    monthChangeEl.className = 'kpi-change ' + (monthChange >= 0 ? 'positive' : 'negative');

    const quarterData = data.slice(-3);
    const quarterAvg = quarterData.reduce((sum, d) => sum + d.value, 0) / quarterData.length;
    document.getElementById('quarterAvg').textContent = indicator.format(quarterAvg) + indicator.unit;

    const quarterChange = ((latestData.value - quarterAvg) / Math.abs(quarterAvg)) * 100;
    const quarterChangeEl = document.getElementById('quarterChange');
    quarterChangeEl.textContent = (quarterChange >= 0 ? '+' : '') + quarterChange.toFixed(2) + '%';
    quarterChangeEl.className = 'kpi-change ' + (quarterChange >= 0 ? 'positive' : 'negative');

    document.getElementById('annualTarget').textContent =
        indicator.annualTarget + indicator.unit;

    const targetProgress = (latestData.value / indicator.annualTarget) * 100;
    const progressClamped = Math.min(100, Math.max(0, targetProgress));
    document.getElementById('targetProgress').textContent = progressClamped.toFixed(1) + '%';

    const trendEl = document.getElementById('targetTrend');
    if (targetProgress >= 100) {
        trendEl.textContent = '✓';
        trendEl.className = 'kpi-trend positive';
    } else if (targetProgress >= 80) {
        trendEl.textContent = '→';
        trendEl.className = 'kpi-trend neutral';
    } else {
        trendEl.textContent = '!';
        trendEl.className = 'kpi-trend negative';
    }

    const minVal = indicator.range.min;
    const maxVal = indicator.range.max;
    const percentile = ((latestData.value - minVal) / (maxVal - minVal)) * 100;
    document.getElementById('percentileValue').textContent = percentile.toFixed(1) + '%';
    document.getElementById('range5y').textContent =
        minVal.toFixed(1) + ' ~ ' + maxVal.toFixed(1) + indicator.unit;
}

function createTrendChart() {
    const ctx = document.getElementById('trendChart').getContext('2d');
    const data = getFilteredData(currentIndicator, currentTimeRange);
    const indicator = macroeconomicData.indicators[currentIndicator];

    if (charts.trend) {
        charts.trend.destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(108, 92, 231, 0.4)');
    gradient.addColorStop(1, 'rgba(108, 92, 231, 0.0)');

    charts.trend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                label: indicator.name,
                data: data.map(d => d.value),
                borderColor: '#6C5CE7',
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: '#6C5CE7',
                pointBorderColor: '#FFFFFF',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 30, 47, 0.95)',
                    titleColor: '#FFFFFF',
                    bodyColor: '#E0E0E0',
                    padding: 14,
                    cornerRadius: 10,
                    displayColors: false,
                    borderColor: 'rgba(108, 92, 231, 0.5)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return indicator.name + ': ' + indicator.format(context.parsed.y) + indicator.unit;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9CA3AF',
                        font: {
                            size: 12
                        }
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.06)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9CA3AF',
                        font: {
                            size: 12
                        },
                        callback: function(value) {
                            return indicator.format(value) + indicator.unit;
                        }
                    }
                }
            }
        }
    });
}

function createYoYChart() {
    const ctx = document.getElementById('yoyChart').getContext('2d');
    const data = getFilteredData(currentIndicator, currentTimeRange);

    if (charts.yoy) {
        charts.yoy.destroy();
    }

    charts.yoy = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                label: '同比变化',
                data: data.map(d => d.yoy),
                backgroundColor: data.map(d => d.yoy >= 0 ? '#FFA500' : '#4CAF50'),
                borderRadius: 6,
                borderSkipped: false,
                hoverBackgroundColor: data.map(d => d.yoy >= 0 ? '#FFB74D' : '#66BB6A')
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 30, 47, 0.95)',
                    titleColor: '#FFFFFF',
                    bodyColor: '#E0E0E0',
                    padding: 14,
                    cornerRadius: 10,
                    callbacks: {
                        label: function(context) {
                            return '同比: ' + (context.parsed.y >= 0 ? '+' : '') + context.parsed.y.toFixed(2) + '%';
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9CA3AF',
                        maxRotation: 45,
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.06)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9CA3AF',
                        callback: function(value) {
                            return value.toFixed(0) + '%';
                        }
                    }
                }
            }
        }
    });
}

function createDistributionChart() {
    const ctx = document.getElementById('distributionChart').getContext('2d');
    const data = getFilteredData(currentIndicator, currentTimeRange);

    if (charts.distribution) {
        charts.distribution.destroy();
    }

    const values = data.map(d => d.value);
    const histogram = createHistogram(values, 10);

    charts.distribution = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: histogram.labels,
            datasets: [{
                data: histogram.counts,
                backgroundColor: [
                    '#6C5CE7', '#8B7CF5', '#A29BFE', '#BDB2FF',
                    '#D9CDFF', '#E8E4FF', '#F0EDFF', '#F5F3FF',
                    '#E0D9FF', '#C9BEFF'
                ],
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 14,
                        padding: 12,
                        font: {
                            size: 11
                        },
                        color: '#6B7280',
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 30, 47, 0.95)',
                    titleColor: '#FFFFFF',
                    bodyColor: '#E0E0E0',
                    padding: 14,
                    cornerRadius: 10,
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed + '次';
                        }
                    }
                }
            }
        }
    });
}

function createHistogram(values, bins) {
    const min = Math.min(...values);
    const max = Math.max(...values);
    const binWidth = (max - min) / bins;

    const histogram = {
        labels: [],
        counts: new Array(bins).fill(0)
    };

    for (let i = 0; i < bins; i++) {
        const binStart = min + i * binWidth;
        const binEnd = binStart + binWidth;
        histogram.labels.push(binStart.toFixed(1) + '-' + binEnd.toFixed(1));
    }

    values.forEach(value => {
        let binIndex = Math.floor((value - min) / binWidth);
        if (binIndex >= bins) binIndex = bins - 1;
        histogram.counts[binIndex]++;
    });

    return histogram;
}

function updateDataTable() {
    const data = getFilteredData();
    const tableBody = document.getElementById('tableBody');
    const paginationInfo = document.getElementById('paginationInfo');
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');

    const itemsPerPage = 10;
    const totalPages = Math.ceil(data.length / itemsPerPage);
    const currentPage = Math.min(window.currentPage || 1, totalPages || 1);
    window.currentPage = currentPage;

    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageData = data.slice(startIndex, endIndex);

    tableBody.innerHTML = pageData.map((item, index) => `
        <tr>
            <td>${item.date}</td>
            <td>${item.value.toFixed(2)}</td>
            <td>${item.mom !== null ? item.mom.toFixed(2) + '%' : '-'}</td>
            <td>${item.yoy !== null ? item.yoy.toFixed(2) + '%' : '-'}</td>
            <td>${item.percentile !== null ? item.percentile.toFixed(0) + '%' : '-'}</td>
        </tr>
    `).join('');

    paginationInfo.textContent = `显示 ${startIndex + 1}-${Math.min(endIndex, data.length)} 条，共 ${data.length} 条`;
    pageInfo.textContent = `第 ${currentPage} 页，共 ${totalPages} 页`;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
}

function changePage(delta) {
    const data = getFilteredData();
    const itemsPerPage = 10;
    const totalPages = Math.ceil(data.length / itemsPerPage);
    const currentPage = Math.min(Math.max((window.currentPage || 1) + delta, 1), totalPages);
    window.currentPage = currentPage;
    updateDataTable();
}

function exportToCSV() {
    const data = getFilteredData(currentIndicator, currentTimeRange);
    const indicator = macroeconomicData.indicators[currentIndicator];

    const headers = ['日期', '指标值', '环比变化', '同比变化', '分位值'];
    const rows = data.map(d => [
        d.date,
        indicator.format(d.value) + indicator.unit,
        d.mom.toFixed(2) + '%',
        d.yoy.toFixed(2) + '%',
        (d.percentile * 100).toFixed(1) + '%'
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${indicator.name}_数据_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
}

function switchChartView(view) {
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    const ctx = document.getElementById('trendChart').getContext('2d');
    const data = getFilteredData(currentIndicator, currentTimeRange);
    const indicator = macroeconomicData.indicators[currentIndicator];

    if (charts.trend) {
        charts.trend.destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(108, 92, 231, 0.4)');
    gradient.addColorStop(1, 'rgba(108, 92, 231, 0.0)');

    charts.trend = new Chart(ctx, {
        type: view,
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                label: indicator.name,
                data: data.map(d => d.value),
                borderColor: '#6C5CE7',
                backgroundColor: view === 'line' ? gradient : 'rgba(108, 92, 231, 0.8)',
                borderWidth: 3,
                fill: view === 'line',
                tension: 0.4,
                pointRadius: view === 'line' ? 5 : 0,
                pointHoverRadius: 7,
                pointBackgroundColor: '#6C5CE7',
                pointBorderColor: '#FFFFFF',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 30, 47, 0.95)',
                    titleColor: '#FFFFFF',
                    bodyColor: '#E0E0E0',
                    padding: 14,
                    cornerRadius: 10,
                    displayColors: false,
                    borderColor: 'rgba(108, 92, 231, 0.5)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return indicator.name + ': ' + indicator.format(context.parsed.y) + indicator.unit;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9CA3AF',
                        font: {
                            size: 12
                        }
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.06)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9CA3AF',
                        font: {
                            size: 12
                        },
                        callback: function(value) {
                            return indicator.format(value) + indicator.unit;
                        }
                    }
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    initializeData();
    updateKPICards();
    updateAllCharts();
    updateDataTable();

    document.querySelectorAll('.indicator-item').forEach(item => {
        item.addEventListener('click', function() {
            handleIndicatorChange(this.dataset.indicator);
        });
    });

    document.getElementById('regionSelect').addEventListener('change', function() {
        handleRegionChange(this.value);
    });

    document.getElementById('timeRangeSelect').addEventListener('change', function() {
        handleTimeRangeChange(this.value);
    });

    document.getElementById('refreshBtn').addEventListener('click', function() {
        initializeData();
        updateKPICards();
        updateAllCharts();
        updateDataTable();
    });

    document.getElementById('exportBtn').addEventListener('click', exportToCSV);

    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchChartView(this.dataset.view);
        });
    });
});

function updateAllCharts() {
    createTrendChart();
    createYoYChart();
    createDistributionChart();
}

function updateLastUpdateTime() {
    const now = new Date();
    const formattedTime = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
    document.getElementById('lastUpdate').textContent = formattedTime;
}

function handleIndicatorChange(indicator) {
    currentIndicator = indicator;
    window.currentPage = 1;

    document.querySelectorAll('.indicator-item').forEach(item => {
        item.classList.toggle('active', item.dataset.indicator === indicator);
    });

    updateKPICards();
    updateAllCharts();
    updateDataTable();
}

function handleTimeRangeChange(range) {
    currentTimeRange = range;
    updateKPICards();
    updateAllCharts();
    updateDataTable();
}

function handleRegionChange(region) {
    currentRegion = region;
    initializeData();
    updateKPICards();
    updateAllCharts();
    updateDataTable();
}
