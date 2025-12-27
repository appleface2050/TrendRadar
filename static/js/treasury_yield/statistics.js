/**
 * 统计计算模块
 * 负责计算各种统计指标
 */

const Statistics = (function() {

    /**
     * 计算单个期限的基础统计
     * @param {Array} data - 数据数组
     * @param {string} tenor - 期限 (如 'DGS10')
     * @returns {Object} 统计结果 {mean, median, min, max, stdDev, variance, count}
     */
    function calculateTenorStats(data, tenor) {
        const values = data
            .map(row => row[tenor])
            .filter(v => v !== null && !isNaN(v));

        if (values.length === 0) {
            return null;
        }

        const sorted = [...values].sort((a, b) => a - b);
        const count = values.length;
        const sum = values.reduce((acc, v) => acc + v, 0);
        const mean = sum / count;
        const min = sorted[0];
        const max = sorted[count - 1];

        // 中位数
        const median = count % 2 === 0
            ? (sorted[count / 2 - 1] + sorted[count / 2]) / 2
            : sorted[Math.floor(count / 2)];

        // 方差和标准差
        const variance = values.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / count;
        const stdDev = Math.sqrt(variance);

        return {
            mean,
            median,
            min,
            max,
            variance,
            stdDev,
            count
        };
    }

    /**
     * 批量计算多个期限的统计
     * @param {Array} data - 数据数组
     * @param {Array} tenors - 期限数组
     * @returns {Object} 各期限统计 {DGS1: {...}, DGS2: {...}, ...}
     */
    function calculateAllTenorStats(data, tenors) {
        const result = {};

        tenors.forEach(tenor => {
            result[tenor] = calculateTenorStats(data, tenor);
        });

        return result;
    }

    /**
     * 计算分位数
     * @param {Array} data - 数据数组
     * @param {string} tenor - 期限
     * @param {Array} percentiles - 分位数数组 (如 [25, 50, 75, 90, 95])
     * @returns {Object} 分位数结果
     */
    function calculatePercentiles(data, tenor, percentiles = [25, 50, 75, 90, 95]) {
        const values = data
            .map(row => row[tenor])
            .filter(v => v !== null && !isNaN(v))
            .sort((a, b) => a - b);

        if (values.length === 0) {
            return null;
        }

        const result = {};

        percentiles.forEach(p => {
            const index = (p / 100) * (values.length - 1);
            const lower = Math.floor(index);
            const upper = Math.ceil(index);
            const weight = index - lower;

            if (lower === upper) {
                result[`p${p}`] = values[lower];
            } else {
                result[`p${p}`] = values[lower] * (1 - weight) + values[upper] * weight;
            }
        });

        return result;
    }

    /**
     * 批量计算多个期限的分位数
     * @param {Array} data - 数据数组
     * @param {Array} tenors - 期限数组
     * @param {Array} percentiles - 分位数数组
     * @returns {Object} 各期限分位数 {DGS1: {...}, DGS2: {...}, ...}
     */
    function calculateAllTenorPercentiles(data, tenors, percentiles = [25, 50, 75, 90, 95]) {
        const result = {};

        tenors.forEach(tenor => {
            result[tenor] = calculatePercentiles(data, tenor, percentiles);
        });

        return result;
    }

    /**
     * 计算滚动标准差
     * @param {Array} data - 数据数组
     * @param {string} tenor - 期限
     * @param {number} window - 窗口大小
     * @returns {Array} 滚动标准差数组 [{date, value}, ...]
     */
    function calculateRollingStd(data, tenor, window = 30) {
        const result = [];

        for (let i = window - 1; i < data.length; i++) {
            const values = [];
            for (let j = i - window + 1; j <= i; j++) {
                if (data[j][tenor] !== null && !isNaN(data[j][tenor])) {
                    values.push(data[j][tenor]);
                }
            }

            if (values.length >= window / 2) { // 至少有一半数据有效
                const mean = values.reduce((acc, v) => acc + v, 0) / values.length;
                const variance = values.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / values.length;
                const stdDev = Math.sqrt(variance);

                result.push({
                    date: data[i].date,
                    value: stdDev
                });
            }
        }

        return result;
    }

    /**
     * 批量计算多个期限的滚动标准差
     * @param {Array} data - 数据数组
     * @param {Array} tenors - 期限数组
     * @param {number} window - 窗口大小
     * @returns {Object} 各期限滚动标准差 {DGS1: [...], DGS2: [...], ...}
     */
    function calculateAllRollingStd(data, tenors, window = 30) {
        const result = {};

        tenors.forEach(tenor => {
            result[tenor] = calculateRollingStd(data, tenor, window);
        });

        return result;
    }

    /**
     * 计算直方图
     * @param {Array} data - 数据数组
     * @param {string} tenor - 期限
     * @param {number} bins - 箱数
     * @returns {Object} 直方图数据 {labels, data}
     */
    function calculateHistogram(data, tenor, bins = 30) {
        const values = data
            .map(row => row[tenor])
            .filter(v => v !== null && !isNaN(v));

        if (values.length === 0) {
            return null;
        }

        const min = Math.min(...values);
        const max = Math.max(...values);
        const binWidth = (max - min) / bins;

        const histogram = new Array(bins).fill(0);
        const labels = [];

        for (let i = 0; i < bins; i++) {
            const binStart = min + i * binWidth;
            const binEnd = binStart + binWidth;
            labels.push((binStart + binEnd) / 2);
        }

        values.forEach(v => {
            let binIndex = Math.floor((v - min) / binWidth);
            if (binIndex >= bins) binIndex = bins - 1;
            if (binIndex < 0) binIndex = 0;
            histogram[binIndex]++;
        });

        return {
            labels: labels.map(l => l.toFixed(2)),
            data: histogram
        };
    }

    /**
     * 格式化基础统计为表格
     * @param {Object} allStats - 各期限统计
     * @returns {string} HTML 表格字符串
     */
    function formatStatsAsTable(allStats) {
        if (!allStats) return '<p>无数据</p>';

        const tenorNames = {
            DGS1: '1年期',
            DGS2: '2年期',
            DGS3: '3年期',
            DGS5: '5年期',
            DGS10: '10年期'
        };

        let html = '<table><thead><tr><th>期限</th><th>均值</th><th>中位数</th><th>最小值</th><th>最大值</th><th>标准差</th></tr></thead><tbody>';

        Object.keys(allStats).forEach(tenor => {
            const stats = allStats[tenor];
            if (stats) {
                html += `<tr>
                    <td>${tenorNames[tenor] || tenor}</td>
                    <td>${stats.mean.toFixed(2)}%</td>
                    <td>${stats.median.toFixed(2)}%</td>
                    <td>${stats.min.toFixed(2)}%</td>
                    <td>${stats.max.toFixed(2)}%</td>
                    <td>${stats.stdDev.toFixed(2)}%</td>
                </tr>`;
            }
        });

        html += '</tbody></table>';
        return html;
    }

    /**
     * 格式化分位数为表格
     * @param {Object} allPercentiles - 各期限分位数
     * @returns {string} HTML 表格字符串
     */
    function formatPercentilesAsTable(allPercentiles) {
        if (!allPercentiles) return '<p>无数据</p>';

        const tenorNames = {
            DGS1: '1年期',
            DGS2: '2年期',
            DGS3: '3年期',
            DGS5: '5年期',
            DGS10: '10年期'
        };

        let html = '<table><thead><tr><th>期限</th><th>P25</th><th>P50</th><th>P75</th><th>P90</th><th>P95</th></tr></thead><tbody>';

        Object.keys(allPercentiles).forEach(tenor => {
            const p = allPercentiles[tenor];
            if (p) {
                html += `<tr>
                    <td>${tenorNames[tenor] || tenor}</td>
                    <td>${p.p25.toFixed(2)}%</td>
                    <td>${p.p50.toFixed(2)}%</td>
                    <td>${p.p75.toFixed(2)}%</td>
                    <td>${p.p90.toFixed(2)}%</td>
                    <td>${p.p95.toFixed(2)}%</td>
                </tr>`;
            }
        });

        html += '</tbody></table>';
        return html;
    }

    // 公共 API
    return {
        calculateTenorStats,
        calculateAllTenorStats,
        calculatePercentiles,
        calculateAllTenorPercentiles,
        calculateRollingStd,
        calculateAllRollingStd,
        calculateHistogram,
        formatStatsAsTable,
        formatPercentilesAsTable
    };
})();
