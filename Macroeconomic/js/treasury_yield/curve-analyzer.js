/**
 * 收益率曲线分析模块
 * 负责计算利差、曲线陡峭度等指标
 */

const CurveAnalyzer = (function() {

    /**
     * 计算利差 (tenor1 - tenor2)
     * @param {Array} data - 数据数组
     * @param {string} tenor1 - 第一个期限 (如 'DGS10')
     * @param {string} tenor2 - 第二个期限 (如 'DGS2')
     * @returns {Array} 利差数组 [{date, value}, ...]
     */
    function calculateSpread(data, tenor1, tenor2) {
        return data.map(row => {
            const v1 = row[tenor1];
            const v2 = row[tenor2];

            if (v1 !== null && v2 !== null) {
                return {
                    date: row.date,
                    value: v1 - v2
                };
            }

            return {
                date: row.date,
                value: null
            };
        }).filter(row => row.value !== null);
    }

    /**
     * 计算曲线陡峭度 (10Y - 2Y 或 10Y - 1Y)
     * @param {Array} data - 数据数组
     * @param {string} shortTenor - 短期限 (如 'DGS2' 或 'DGS1')
     * @param {string} longTenor - 长期限 (默认 'DGS10')
     * @returns {Array} 陡峭度数组 [{date, value}, ...]
     */
    function calculateCurveSteepness(data, shortTenor = 'DGS1', longTenor = 'DGS10') {
        return calculateSpread(data, longTenor, shortTenor);
    }

    /**
     * 获取当前曲线陡峭度
     * @param {Array} data - 数据数组
     * @returns {Object} {date, value} 或 null
     */
    function getCurrentSteepness(data) {
        if (!data || data.length === 0) return null;

        const lastRow = data[data.length - 1];
        const dgs10 = lastRow.DGS10;
        const dgs1 = lastRow.DGS1;

        if (dgs10 !== null && dgs1 !== null) {
            return {
                date: lastRow.date,
                value: dgs10 - dgs1
            };
        }

        return null;
    }

    /**
     * 检测曲线倒挂 (短期 > 长期)
     * @param {Array} data - 数据数组
     * @param {string} shortTenor - 短期限
     * @param {string} longTenor - 长期限
     * @returns {Array} 倒挂数据点 [{date, shortValue, longValue, spread}, ...]
     */
    function detectInversion(data, shortTenor = 'DGS2', longTenor = 'DGS10') {
        return data.filter(row => {
            const short = row[shortTenor];
            const long = row[longTenor];
            return short !== null && long !== null && short > long;
        }).map(row => ({
            date: row.date,
            shortValue: row[shortTenor],
            longValue: row[longTenor],
            spread: row[longTenor] - row[shortTenor]
        }));
    }

    /**
     * 获取最新期限结构数据
     * @param {Array} data - 数据数组
     * @param {Array} tenors - 期限数组
     * @returns {Object} 最新期限结构 {date, DGS1, DGS2, ...}
     */
    function getLatestTermStructure(data, tenors = ['DGS1', 'DGS2', 'DGS3', 'DGS5', 'DGS10']) {
        if (!data || data.length === 0) return null;

        // 从后向前找第一个所有期限都有值的数据点
        for (let i = data.length - 1; i >= 0; i--) {
            const row = data[i];
            const allValid = tenors.every(tenor => row[tenor] !== null);

            if (allValid) {
                const result = { date: row.date };
                tenors.forEach(tenor => {
                    result[tenor] = row[tenor];
                });
                return result;
            }
        }

        return null;
    }

    /**
     * 计算各期限与10Y的利差
     * @param {Array} data - 数据数组
     * @param {Array} tenors - 期限数组
     * @returns {Object} 各期限利差 {DGS1: [{date, value}, ...], DGS2: [...], ...}
     */
    function calculateSpreadsTo10Y(data, tenors = ['DGS1', 'DGS2', 'DGS3', 'DGS5']) {
        const result = {};

        tenors.forEach(tenor => {
            result[tenor] = data.map(row => {
                const v10y = row.DGS10;
                const vTenor = row[tenor];

                if (v10y !== null && vTenor !== null) {
                    return {
                        date: row.date,
                        value: vTenor - v10y
                    };
                }

                return {
                    date: row.date,
                    value: null
                };
            }).filter(row => row.value !== null);
        });

        return result;
    }

    /**
     * 计算各期限当前值
     * @param {Array} data - 数据数组
     * @param {Array} tenors - 期限数组
     * @returns {Object} 各期限当前值 {DGS1: value, DGS2: value, ...}
     */
    function getCurrentValues(data, tenors = ['DGS1', 'DGS2', 'DGS3', 'DGS5', 'DGS10']) {
        if (!data || data.length === 0) {
            const result = {};
            tenors.forEach(tenor => result[tenor] = null);
            return result;
        }

        const result = {};
        tenors.forEach(tenor => {
            // 从后向前找第一个有效值
            for (let i = data.length - 1; i >= 0; i--) {
                if (data[i][tenor] !== null) {
                    result[tenor] = data[i][tenor];
                    return;
                }
            }
            result[tenor] = null;
        });

        return result;
    }

    // 公共 API
    return {
        calculateSpread,
        calculateCurveSteepness,
        getCurrentSteepness,
        detectInversion,
        getLatestTermStructure,
        calculateSpreadsTo10Y,
        getCurrentValues
    };
})();
