/**
 * 收益率曲线倒挂分析模块
 * 负责检测和分析收益率曲线倒挂（10y-2y < 0）期间
 */

const InversionAnalyzer = (function() {

    /**
     * 检测所有倒挂期
     * @param {Array} data - 数据数组
     * @param {number} minDays - 最小持续天数（默认30天）
     * @returns {Array} 倒挂期数组
     */
    function detectInversions(data, minDays = 30) {
        const periods = [];
        let inInversion = false;
        let currentPeriod = null;

        data.forEach((point, index) => {
            const isInversion = point.value < 0;

            if (isInversion && !inInversion) {
                // 开始新的倒挂期
                currentPeriod = {
                    startDate: point.date,
                    endDate: null,
                    minValue: point.value,
                    minDate: point.date,
                    days: 1
                };
                inInversion = true;
            } else if (isInversion && inInversion) {
                // 继续倒挂期
                currentPeriod.days++;
                if (point.value < currentPeriod.minValue) {
                    currentPeriod.minValue = point.value;
                    currentPeriod.minDate = point.date;
                }
                currentPeriod.endDate = point.date;
            } else if (!isInversion && inInversion) {
                // 结束倒挂期
                if (currentPeriod.days >= minDays) {
                    periods.push({ ...currentPeriod });
                }
                currentPeriod = null;
                inInversion = false;
            }
        });

        // 处理数据结束时仍在倒挂期的情况
        if (inInversion && currentPeriod && currentPeriod.days >= minDays) {
            periods.push({ ...currentPeriod });
        }

        return periods;
    }

    /**
     * 获取当前倒挂状态
     * @param {Array} data - 数据数组
     * @returns {Object} 当前倒挂状态
     */
    function getCurrentInversionStatus(data) {
        if (!data || data.length === 0) {
            return { isInverted: false, days: 0 };
        }

        const lastPoint = data[data.length - 1];
        const isInverted = lastPoint.value < 0;

        if (!isInverted) {
            return { isInverted: false, days: 0 };
        }

        // 计算当前倒挂持续天数
        let days = 0;
        for (let i = data.length - 1; i >= 0; i--) {
            if (data[i].value < 0) {
                days++;
            } else {
                break;
            }
        }

        return {
            isInverted: true,
            days,
            currentValue: lastPoint.value
        };
    }

    /**
     * 计算倒挂统计
     * @param {Array} data - 数据数组
     * @param {number} minDays - 最小持续天数
     * @returns {Object} 倒挂统计信息
     */
    function calculateInversionStats(data, minDays = 30) {
        const totalDays = data.length;
        const periods = detectInversions(data, minDays);

        const totalInversionDays = periods.reduce((sum, p) => sum + p.days, 0);
        const inversionRatio = ((totalInversionDays / totalDays) * 100).toFixed(2);

        // 最长和平均持续期
        const maxDuration = periods.length > 0
            ? Math.max(...periods.map(p => p.days))
            : 0;

        const avgDuration = periods.length > 0
            ? (totalInversionDays / periods.length).toFixed(1)
            : 0;

        // 最严重的倒挂（最小值）
        const mostSevere = periods.length > 0
            ? periods.reduce((min, p) =>
                p.minValue < min.minValue ? p : min
            )
            : null;

        return {
            totalDays,
            inversionDays: totalInversionDays,
            nonInversionDays: totalDays - totalInversionDays,
            inversionRatio: parseFloat(inversionRatio),
            periodsCount: periods.length,
            maxDuration,
            avgDuration: parseFloat(avgDuration),
            mostSevere: mostSevere ? {
                date: mostSevere.minDate,
                value: mostSevere.minValue
            } : null,
            periods
        };
    }

    /**
     * 为图表标注准备倒挂区域数据
     * @param {Array} data - 数据数组
     * @param {number} minDays - 最小持续天数
     * @returns {Array} 标注数据（用于 Chart.js annotation plugin）
     */
    function prepareInversionAnnotations(data, minDays = 30) {
        const periods = detectInversions(data, minDays);
        const annotations = {};

        periods.forEach((period, index) => {
            annotations[`inversion${index}`] = {
                type: 'box',
                xMin: period.startDate,
                xMax: period.endDate,
                yMin: -5,
                yMax: 0,
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderColor: 'rgba(239, 68, 68, 0.3)',
                borderWidth: 1
            };
        });

        return annotations;
    }

    /**
     * 获取倒挂期汇总数据（用于柱状图展示）
     * @param {Array} data - 数据数组
     * @param {number} minDays - 最小持续天数
     * @returns {Object} 倒挂期汇总数据
     */
    function getInversionSummary(data, minDays = 30) {
        const periods = detectInversions(data, minDays);

        return {
            labels: periods.map((p, i) => `倒挂期 ${i + 1}`),
            data: periods.map(p => p.days),
            tooltips: periods.map(p => ({
                startDate: p.startDate,
                endDate: p.endDate,
                days: p.days,
                minValue: p.minValue,
                minDate: p.minDate
            }))
        };
    }

    /**
     * 检查特定日期是否在倒挂期
     * @param {string} date - 日期 (YYYY-MM-DD)
     * @param {Array} data - 数据数组
     * @returns {boolean} 是否在倒挂期
     */
    function isInvertedOn(date, data) {
        const point = data.find(p => p.date === date);
        return point ? point.value < 0 : false;
    }

    /**
     * 获取倒挂期的详细描述
     * @param {Array} data - 数据数组
     * @returns {Array} 倒挂期详细描述数组
     */
    function getInversionDescriptions(data) {
        const periods = detectInversions(data, 30);

        return periods.map((period, index) => {
            const startDate = new Date(period.startDate);
            const endDate = new Date(period.endDate);

            return {
                index: index + 1,
                startDate: period.startDate,
                endDate: period.endDate,
                days: period.days,
                minValue: period.minValue,
                minDate: period.minDate,
                description: `${startDate.getFullYear()}年倒挂期`
            };
        });
    }

    // 公共 API
    return {
        detectInversions,
        getCurrentInversionStatus,
        calculateInversionStats,
        prepareInversionAnnotations,
        getInversionSummary,
        isInvertedOn,
        getInversionDescriptions
    };
})();
