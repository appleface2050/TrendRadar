/**
 * 对比分析模块
 * 负责不同时期的数据对比分析
 */

const Comparison = (function() {

    // NBER 定义的美国经济衰退时期
    const RECESSION_PERIODS = [
        { start: '1980-01-01', end: '1980-07-01' },
        { start: '1981-07-01', end: '1982-11-01' },
        { start: '1990-07-01', end: '1991-03-01' },
        { start: '2001-03-01', end: '2001-11-01' },
        { start: '2007-12-01', end: '2009-06-01' },
        { start: '2020-02-01', end: '2020-04-01' }
    ];

    /**
     * 按年代分组数据
     * @param {Array} data - 数据数组
     * @returns {Object} 年代分组数据
     */
    function compareByDecade(data) {
        const decades = {};

        data.forEach(point => {
            const year = new Date(point.date).getFullYear();
            const decade = Math.floor(year / 10) * 10;
            const decadeLabel = `${decade}s`;

            if (!decades[decadeLabel]) {
                decades[decadeLabel] = {
                    label: decadeLabel,
                    values: [],
                    count: 0,
                    inversionDays: 0
                };
            }

            decades[decadeLabel].values.push(point.value);
            decades[decadeLabel].count++;

            if (point.value < 0) {
                decades[decadeLabel].inversionDays++;
            }
        });

        // 计算统计指标
        const result = [];
        for (const decade of Object.values(decades)) {
            const values = decade.values;
            const sum = values.reduce((a, b) => a + b, 0);
            const avg = sum / values.length;
            const inversionRatio = (decade.inversionDays / decade.count) * 100;

            result.push({
                decade: decade.label,
                avgSpread: parseFloat(avg.toFixed(3)),
                inversionRatio: parseFloat(inversionRatio.toFixed(2)),
                count: decade.count,
                min: Math.min(...values),
                max: Math.max(...values)
            });
        }

        // 按年代排序
        result.sort((a, b) => parseInt(a.decade) - parseInt(b.decade));

        return {
            labels: result.map(d => d.decade),
            avgSpread: result.map(d => d.avgSpread),
            inversionRatio: result.map(d => d.inversionRatio),
            details: result
        };
    }

    /**
     * 衰退前后对比
     * @param {Array} data - 数据数组
     * @param {number} monthsBefore - 衰退前月数
     * @param {number} monthsAfter - 衰退后月数
     * @returns {Object} 衰退对比数据
     */
    function compareByRecession(data, monthsBefore = 6, monthsAfter = 6) {
        const results = [];

        RECESSION_PERIODS.forEach(period => {
            const startDate = new Date(period.start);
            const endDate = new Date(period.end);

            // 计算衰退前、中、后的日期范围
            const preDate = new Date(startDate);
            preDate.setMonth(preDate.getMonth() - monthsBefore);

            const postDate = new Date(endDate);
            postDate.setMonth(postDate.getMonth() + monthsAfter);

            // 筛选各时期数据
            const preData = data.filter(d => {
                const date = new Date(d.date);
                return date >= preDate && date < startDate;
            });

            const duringData = data.filter(d => {
                const date = new Date(d.date);
                return date >= startDate && date <= endDate;
            });

            const postData = data.filter(d => {
                const date = new Date(d.date);
                return date > endDate && date <= postDate;
            });

            // 计算统计
            const calcStats = (arr) => {
                if (arr.length === 0) return null;
                const values = arr.map(d => d.value);
                const sum = values.reduce((a, b) => a + b, 0);
                return {
                    avg: parseFloat((sum / values.length).toFixed(3)),
                    min: Math.min(...values),
                    max: Math.max(...values),
                    count: values.length
                };
            };

            results.push({
                recession: `${startDate.getFullYear()}-${endDate.getFullYear()}`,
                pre: calcStats(preData),
                during: calcStats(duringData),
                post: calcStats(postData),
                startDate: period.start,
                endDate: period.end
            });
        });

        return {
            labels: results.map(r => r.recession),
            preAvg: results.map(r => r.pre ? r.pre.avg : 0),
            duringAvg: results.map(r => r.during ? r.during.avg : 0),
            postAvg: results.map(r => r.post ? r.post.avg : 0),
            details: results
        };
    }

    /**
     * 季节性分析
     * @param {Array} data - 数据数组
     * @returns {Object} 季节性数据
     */
    function analyzeSeasonality(data) {
        const monthlyStats = {};

        // 初始化月度统计
        for (let m = 1; m <= 12; m++) {
            monthlyStats[m] = {
                month: m,
                monthName: `${m}月`,
                values: [],
                inversionCount: 0
            };
        }

        // 按月分组
        data.forEach(point => {
            const date = new Date(point.date);
            const month = date.getMonth() + 1;

            monthlyStats[month].values.push(point.value);
            if (point.value < 0) {
                monthlyStats[month].inversionCount++;
            }
        });

        // 计算统计
        const result = [];
        for (let m = 1; m <= 12; m++) {
            const stats = monthlyStats[m];
            const values = stats.values;

            if (values.length > 0) {
                const sum = values.reduce((a, b) => a + b, 0);
                const avg = sum / values.length;
                const inversionRatio = (stats.inversionCount / values.length) * 100;

                result.push({
                    month: stats.monthName,
                    avgSpread: parseFloat(avg.toFixed(3)),
                    inversionRatio: parseFloat(inversionRatio.toFixed(2)),
                    min: Math.min(...values),
                    max: Math.max(...values),
                    count: values.length
                });
            }
        }

        return {
            labels: result.map(r => r.month),
            avgSpread: result.map(r => r.avgSpread),
            inversionRatio: result.map(r => r.inversionRatio),
            details: result
        };
    }

    /**
     * 按时期分组数据（通用函数）
     * @param {Array} data - 数据数组
     * @param {string} periodType - 时期类型 ('decade', 'year', 'quarter', 'month')
     * @returns {Object} 分组数据
     */
    function groupByPeriod(data, periodType) {
        const grouped = {};

        data.forEach(point => {
            const date = new Date(point.date);
            let key;

            switch (periodType) {
                case 'decade':
                    const decade = Math.floor(date.getFullYear() / 10) * 10;
                    key = `${decade}s`;
                    break;
                case 'year':
                    key = date.getFullYear().toString();
                    break;
                case 'quarter':
                    const quarter = Math.floor(date.getMonth() / 3) + 1;
                    key = `${date.getFullYear()}-Q${quarter}`;
                    break;
                case 'month':
                    key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                    break;
                default:
                    key = date.getFullYear().toString();
            }

            if (!grouped[key]) {
                grouped[key] = {
                    period: key,
                    values: [],
                    dates: []
                };
            }

            grouped[key].values.push(point.value);
            grouped[key].dates.push(point.date);
        });

        // 计算每个时期的统计
        const result = Object.values(grouped).map(g => {
            const values = g.values;
            const sum = values.reduce((a, b) => a + b, 0);

            return {
                period: g.period,
                avg: parseFloat((sum / values.length).toFixed(3)),
                min: Math.min(...values),
                max: Math.max(...values),
                count: values.length,
                startDate: g.dates[0],
                endDate: g.dates[g.dates.length - 1]
            };
        });

        // 按时期排序
        result.sort((a, b) => a.period.localeCompare(b.period));

        return result;
    }

    /**
     * 计算时期之间的变化率
     * @param {Array} periodData - 时期数据
     * @returns {Array} 变化率数据
     */
    function calculatePeriodChange(periodData) {
        const changes = [];

        for (let i = 1; i < periodData.length; i++) {
            const current = periodData[i];
            const previous = periodData[i - 1];

            const change = current.avg - previous.avg;
            const changePercent = ((change / Math.abs(previous.avg)) * 100);

            changes.push({
                period: current.period,
                change: parseFloat(change.toFixed(3)),
                changePercent: parseFloat(changePercent.toFixed(2))
            });
        }

        return changes;
    }

    /**
     * 格式化对比数据为表格HTML
     * @param {Array} data - 对比数据
     * @param {string} type - 对比类型
     * @returns {string} HTML表格字符串
     */
    function formatComparisonAsTable(data, type) {
        if (!data || data.length === 0) {
            return '<p>无数据</p>';
        }

        let html = '<table><thead><tr>';

        // 表头
        switch (type) {
            case 'decade':
                html += '<th>年代</th><th>平均利差 (%)</th><th>倒挂比例 (%)</th><th>数据点数</th>';
                break;
            case 'recession':
                html += '<th>衰退期</th><th>前6月均值</th><th>期间均值</th><th>后6月均值</th>';
                break;
            case 'seasonality':
                html += '<th>月份</th><th>平均利差 (%)</th><th>倒挂比例 (%)</th>';
                break;
            default:
                html += '<th>时期</th><th>平均值</th>';
        }

        html += '</tr></thead><tbody>';

        // 数据行
        data.forEach(item => {
            html += '<tr>';
            switch (type) {
                case 'decade':
                    html += `<td>${item.decade}</td>`;
                    html += `<td>${item.avgSpread}</td>`;
                    html += `<td>${item.inversionRatio}</td>`;
                    html += `<td>${item.count}</td>`;
                    break;
                case 'recession':
                    html += `<td>${item.recession}</td>`;
                    html += `<td>${item.pre ? item.pre.avg : 'N/A'}</td>`;
                    html += `<td>${item.during ? item.during.avg : 'N/A'}</td>`;
                    html += `<td>${item.post ? item.post.avg : 'N/A'}</td>`;
                    break;
                case 'seasonality':
                    html += `<td>${item.month}</td>`;
                    html += `<td>${item.avgSpread}</td>`;
                    html += `<td>${item.inversionRatio}</td>`;
                    break;
                default:
                    html += `<td>${item.period}</td>`;
                    html += `<td>${item.avg}</td>`;
            }
            html += '</tr>';
        });

        html += '</tbody></table>';

        return html;
    }

    // 公共 API
    return {
        compareByDecade,
        compareByRecession,
        analyzeSeasonality,
        groupByPeriod,
        calculatePeriodChange,
        formatComparisonAsTable,
        get RECESSION_PERIODS() { return RECESSION_PERIODS; }
    };
})();
