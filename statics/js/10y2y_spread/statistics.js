/**
 * 统计分析模块
 * 负责计算各种统计指标
 */

const Statistics = (function() {

    /**
     * 计算基础统计指标
     * @param {Array} data - 数据数组
     * @returns {Object} 基础统计指标
     */
    function calculateBasicStats(data) {
        if (!data || data.length === 0) {
            return null;
        }

        const values = data.map(d => d.value);
        const n = values.length;

        // 排序用于计算分位数
        const sorted = [...values].sort((a, b) => a - b);

        // 均值
        const mean = values.reduce((sum, v) => sum + v, 0) / n;

        // 中位数
        const median = n % 2 === 0
            ? (sorted[n / 2 - 1] + sorted[n / 2]) / 2
            : sorted[Math.floor(n / 2)];

        // 极值
        const min = sorted[0];
        const max = sorted[n - 1];

        // 方差和标准差
        const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / n;
        const stdDev = Math.sqrt(variance);

        // 变异系数
        const cv = mean !== 0 ? (stdDev / Math.abs(mean) * 100) : 0;

        return {
            count: n,
            mean: parseFloat(mean.toFixed(3)),
            median: parseFloat(median.toFixed(3)),
            min: parseFloat(min.toFixed(3)),
            max: parseFloat(max.toFixed(3)),
            range: parseFloat((max - min).toFixed(3)),
            variance: parseFloat(variance.toFixed(4)),
            stdDev: parseFloat(stdDev.toFixed(3)),
            cv: parseFloat(cv.toFixed(2))
        };
    }

    /**
     * 计算分位数
     * @param {Array} data - 数据数组
     * @param {Array} percentiles - 分位数数组，如 [25, 50, 75, 90, 95]
     * @returns {Object} 分位数结果
     */
    function calculatePercentiles(data, percentiles = [25, 50, 75, 90, 95]) {
        if (!data || data.length === 0) {
            return null;
        }

        const values = data.map(d => d.value).sort((a, b) => a - b);
        const n = values.length;
        const result = {};

        percentiles.forEach(p => {
            const index = (p / 100) * (n - 1);
            const lower = Math.floor(index);
            const upper = Math.ceil(index);
            const weight = index - lower;

            const value = lower === upper
                ? values[lower]
                : values[lower] * (1 - weight) + values[upper] * weight;

            result[`p${p}`] = parseFloat(value.toFixed(3));
        });

        return result;
    }

    /**
     * 计算滚动标准差
     * @param {Array} data - 数据数组
     * @param {number} window - 窗口大小（默认30天）
     * @returns {Array} 滚动标准差数组
     */
    function calculateRollingStd(data, window = 30) {
        if (!data || data.length < window) {
            return [];
        }

        const result = [];

        for (let i = window - 1; i < data.length; i++) {
            const values = data.slice(i - window + 1, i + 1).map(d => d.value);
            const mean = values.reduce((sum, v) => sum + v, 0) / window;
            const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / window;
            const stdDev = Math.sqrt(variance);

            result.push({
                date: data[i].date,
                value: parseFloat(stdDev.toFixed(3))
            });
        }

        return result;
    }

    /**
     * 计算直方图数据
     * @param {Array} data - 数据数组
     * @param {number} bins - 箱数（默认30）
     * @returns {Object} 直方图数据
     */
    function calculateHistogram(data, bins = 30) {
        if (!data || data.length === 0) {
            return null;
        }

        const values = data.map(d => d.value);
        const min = Math.min(...values);
        const max = Math.max(...values);

        // 计算箱宽度
        const binWidth = (max - min) / bins;

        // 初始化箱
        const histogram = Array(bins).fill(0);
        const labels = [];

        for (let i = 0; i < bins; i++) {
            const binStart = min + i * binWidth;
            const binEnd = binStart + binWidth;
            labels.push(`${binStart.toFixed(2)}`);
        }

        // 分配数据到箱
        values.forEach(value => {
            let binIndex = Math.floor((value - min) / binWidth);
            if (binIndex >= bins) binIndex = bins - 1;
            histogram[binIndex]++;
        });

        return {
            labels,
            data: histogram,
            binWidth,
            min,
            max
        };
    }

    /**
     * 计算同比变化
     * @param {Array} data - 数据数组
     * @param {number} period - 对比周期（默认12个月）
     * @returns {Array} 同比变化数据
     */
    function calculateYoYChange(data, period = 252) { // 假设一年约252个交易日
        if (!data || data.length <= period) {
            return [];
        }

        const result = [];

        for (let i = period; i < data.length; i++) {
            const currentValue = data[i].value;
            const previousValue = data[i - period].value;

            const yoyChange = ((currentValue - previousValue) / Math.abs(previousValue)) * 100;

            result.push({
                date: data[i].date,
                value: parseFloat(yoyChange.toFixed(2))
            });
        }

        return result;
    }

    /**
     * 计算移动平均
     * @param {Array} data - 数据数组
     * @param {number} window - 窗口大小
     * @returns {Array} 移动平均数据
     */
    function calculateMovingAverage(data, window = 30) {
        if (!data || data.length < window) {
            return [];
        }

        const result = [];

        for (let i = window - 1; i < data.length; i++) {
            const values = data.slice(i - window + 1, i + 1).map(d => d.value);
            const avg = values.reduce((sum, v) => sum + v, 0) / window;

            result.push({
                date: data[i].date,
                value: parseFloat(avg.toFixed(3))
            });
        }

        return result;
    }

    /**
     * 计算Z-score
     * @param {Array} data - 数据数组
     * @param {number} window - 滚动窗口大小（默认252个交易日）
     * @returns {Array} Z-score数据
     */
    function calculateZScore(data, window = 252) {
        if (!data || data.length < window) {
            return [];
        }

        const result = [];

        for (let i = window - 1; i < data.length; i++) {
            const values = data.slice(i - window + 1, i + 1).map(d => d.value);
            const mean = values.reduce((sum, v) => sum + v, 0) / window;
            const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / window;
            const stdDev = Math.sqrt(variance);

            const zScore = stdDev !== 0
                ? (data[i].value - mean) / stdDev
                : 0;

            result.push({
                date: data[i].date,
                value: parseFloat(zScore.toFixed(3))
            });
        }

        return result;
    }

    /**
     * 格式化统计指标为表格HTML
     * @param {Object} stats - 统计指标对象
     * @returns {string} HTML表格字符串
     */
    function formatStatsAsTable(stats) {
        if (!stats) {
            return '<p>无数据</p>';
        }

        const labels = {
            count: '数据点数',
            mean: '均值',
            median: '中位数',
            min: '最小值',
            max: '最大值',
            range: '极差',
            variance: '方差',
            stdDev: '标准差',
            cv: '变异系数 (%)'
        };

        let html = '<table><tbody>';

        for (const [key, value] of Object.entries(stats)) {
            if (key !== 'count' && labels[key]) {
                html += `<tr><td>${labels[key]}</td><td>${value}</td></tr>`;
            }
        }

        html += '</tbody></table>';

        return html;
    }

    /**
     * 格式化分位数为表格HTML
     * @param {Object} percentiles - 分位数对象
     * @returns {string} HTML表格字符串
     */
    function formatPercentilesAsTable(percentiles) {
        if (!percentiles) {
            return '<p>无数据</p>';
        }

        let html = '<table><tbody>';

        for (const [key, value] of Object.entries(percentiles)) {
            const label = key.replace('p', 'P');
            html += `<tr><td>${label}</td><td>${value}%</td></tr>`;
        }

        html += '</tbody></table>';

        return html;
    }

    // 公共 API
    return {
        calculateBasicStats,
        calculatePercentiles,
        calculateRollingStd,
        calculateHistogram,
        calculateYoYChange,
        calculateMovingAverage,
        calculateZScore,
        formatStatsAsTable,
        formatPercentilesAsTable
    };
})();
