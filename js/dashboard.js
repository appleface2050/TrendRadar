// Dashboard Application
let charts = {};
let currentData = [];
let sortColumn = 'date';
let sortDirection = 'desc';

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    document.getElementById('lastUpdated').textContent = new Date().toLocaleDateString();
});

function initializeDashboard() {
    // Filter data based on selected time range
    const years = parseInt(document.getElementById('dateRange').value);
    currentData = filterDataByYears(economicData, years);

    // Update KPI cards
    updateKPIs(currentData);

    // Initialize charts
    initializeCharts(currentData);

    // Populate table
    populateTable(currentData);
}

function filterDataByYears(data, years) {
    if (years === 0) return data;

    const cutoffDate = new Date();
    cutoffDate.setFullYear(cutoffDate.getFullYear() - years);

    return data.filter(item => new Date(item.date) >= cutoffDate);
}

function updateKPIs(data) {
    if (data.length === 0) return;

    const latest = data[data.length - 1];
    const previous = data[Math.max(0, data.length - 13)]; // Compare with 12 months ago

    updateKPI('gdp', latest.gdp, previous.gdp, '%');
    updateKPI('inflation', latest.inflation, previous.inflation, '%');
    updateKPI('unemployment', latest.unemployment, previous.unemployment, '%');
    updateKPI('interest', latest.interest, previous.interest, '%');
}

function updateKPI(id, current, previous, suffix) {
    const valueEl = document.getElementById(`${id}-value`);
    const changeEl = document.getElementById(`${id}-change`);

    valueEl.textContent = current.toFixed(1) + suffix;

    const change = current - previous;
    const sign = change >= 0 ? '+' : '';
    changeEl.textContent = `${sign}${change.toFixed(1)}% vs last year`;

    changeEl.className = 'kpi-change';
    if (change > 0) {
        changeEl.classList.add('positive');
    } else if (change < 0) {
        changeEl.classList.add('negative');
    } else {
        changeEl.classList.add('neutral');
    }
}

function initializeCharts(data) {
    const labels = data.map(item => {
        const date = new Date(item.date);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    });

    // GDP Chart
    charts.gdp = createChart('gdpChart', labels, data.map(d => d.gdp),
        'GDP Growth Rate (%)', 'rgba(102, 126, 234, 1)', 'rgba(102, 126, 234, 0.1)');

    // Inflation Chart
    charts.inflation = createChart('inflationChart', labels, data.map(d => d.inflation),
        'Inflation Rate (%)', 'rgba(239, 68, 68, 1)', 'rgba(239, 68, 68, 0.1)');

    // Unemployment Chart
    charts.unemployment = createChart('unemploymentChart', labels, data.map(d => d.unemployment),
        'Unemployment Rate (%)', 'rgba(16, 185, 129, 1)', 'rgba(16, 185, 129, 0.1)');

    // Interest Rate Chart
    charts.interest = createChart('interestChart', labels, data.map(d => d.interest),
        'Interest Rate (%)', 'rgba(245, 158, 11, 1)', 'rgba(245, 158, 11, 0.1)');
}

function createChart(canvasId, labels, data, label, borderColor, backgroundColor) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: borderColor,
                backgroundColor: backgroundColor,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: borderColor,
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: borderColor,
                    borderWidth: 1,
                    cornerRadius: 6,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 12,
                        color: '#666'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        color: '#666',
                        callback: function(value) {
                            return value.toFixed(1) + '%';
                        }
                    }
                }
            }
        }
    });
}

function populateTable(data) {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';

    // Sort data
    const sortedData = [...data].sort((a, b) => {
        let aVal = a[sortColumn];
        let bVal = b[sortColumn];

        if (sortColumn === 'date') {
            aVal = new Date(aVal);
            bVal = new Date(bVal);
        }

        if (sortDirection === 'asc') {
            return aVal > bVal ? 1 : -1;
        } else {
            return aVal < bVal ? 1 : -1;
        }
    });

    sortedData.forEach(item => {
        const row = document.createElement('tr');
        const date = new Date(item.date);

        row.innerHTML = `
            <td>${date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</td>
            <td>${item.gdp.toFixed(1)}%</td>
            <td>${item.inflation.toFixed(1)}%</td>
            <td>${item.unemployment.toFixed(1)}%</td>
            <td>${item.interest.toFixed(2)}%</td>
        `;
        tbody.appendChild(row);
    });
}

function setupEventListeners() {
    // Date range filter
    document.getElementById('dateRange').addEventListener('change', function() {
        const years = parseInt(this.value);
        currentData = filterDataByYears(economicData, years);
        updateDashboard(currentData);
    });

    // Table sorting
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', function() {
            const column = this.getAttribute('data-sort');

            if (sortColumn === column) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                sortColumn = column;
                sortDirection = 'desc';
            }

            populateTable(currentData);
        });
    });
}

function updateDashboard(data) {
    // Update KPIs
    updateKPIs(data);

    // Update charts
    const labels = data.map(item => {
        const date = new Date(item.date);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    });

    charts.gdp.data.labels = labels;
    charts.gdp.data.datasets[0].data = data.map(d => d.gdp);
    charts.gdp.update();

    charts.inflation.data.labels = labels;
    charts.inflation.data.datasets[0].data = data.map(d => d.inflation);
    charts.inflation.update();

    charts.unemployment.data.labels = labels;
    charts.unemployment.data.datasets[0].data = data.map(d => d.unemployment);
    charts.unemployment.update();

    charts.interest.data.labels = labels;
    charts.interest.data.datasets[0].data = data.map(d => d.interest);
    charts.interest.update();

    // Update table
    populateTable(data);
}
