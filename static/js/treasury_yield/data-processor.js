/**
 * 数据加载与处理模块
 * 负责多列 CSV 数据的加载、解析、聚合和筛选
 */

const DataProcessor = (function() {
    // 数据缓存
    const cache = {
        raw: null,           // 原始数据
        day: null,           // 日度数据
        week: null,          // 周度数据
        month: null,         // 月度数据
        current: 'day'       // 当前粒度
    };

    const CSV_URL = '../data/fred_treasury_yield/treasury_yield_daily.csv';

    // 期限定义
    const TENORS = ['DGS1', 'DGS2', 'DGS3', 'DGS5', 'DGS10'];

    /**
     * 加载 CSV 数据
     * @returns {Promise<Array>} 数据对象数组
     */
    async function loadCSVData() {
        if (cache.raw) {
            return cache.raw;
        }

        try {
            const response = await fetch(CSV_URL);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const csvText = await response.text();
            const data = parseMultiColumnCSV(csvText);

            // 缓存原始数据
            cache.raw = data;
            cache.day = data;

            return data;
        } catch (error) {
            console.error('加载 CSV 数据失败:', error);

            // 检测 CORS 错误
            if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
                throw new Error(
                    'CORS 错误：浏览器阻止了跨域请求。\n\n' +
                    '解决方法：\n' +
                    '1. 使用 HTTP 服务器而不是直接打开 HTML 文件\n' +
                    '2. 在 Macroeconomic 目录运行: python -m http.server 8088\n' +
                    '3. 然后访问: http://localhost:8088/display/treasury_yield.html\n\n' +
                    '或者运行以下命令快速启动：\n' +
                    'cd Macroeconomic && python -m http.server 8088'
                );
            }

            throw error;
        }
    }

    /**
     * 解析多列 CSV 文本
     * @param {string} csvText - CSV 文本内容
     * @returns {Array} 解析后的数据对象数组
     */
    function parseMultiColumnCSV(csvText) {
        const lines = csvText.trim().split('\n');
        const data = [];

        // 跳过标题行
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;

            const parts = line.split(',');
            if (parts.length >= 2) {
                const date = parts[0].trim();
                const row = { date };

                // 解析各期限数据
                TENORS.forEach((tenor, index) => {
                    const value = parts[index + 1] ? parts[index + 1].trim() : '';
                    if (value === '' || value === '.') {
                        row[tenor] = null;
                    } else {
                        const numValue = parseFloat(value);
                        row[tenor] = isNaN(numValue) ? null : numValue;
                    }
                });

                data.push(row);
            }
        }

        // 按日期排序
        data.sort((a, b) => new Date(a.date) - new Date(b.date));

        return data;
    }

    /**
     * 空值填充
     * @param {Array} data - 数据数组
     * @param {string} method - 填充方法 ('forward', 'linear', 'none')
     * @returns {Array} 填充后的数据
     */
    function fillMissingValues(data, method = 'forward') {
        if (method === 'none') {
            return data;
        }

        const result = JSON.parse(JSON.stringify(data)); // 深拷贝

        TENORS.forEach(tenor => {
            let lastValidValue = null;
            let nullStartIndex = -1;

            for (let i = 0; i < result.length; i++) {
                if (result[i][tenor] !== null) {
                    // 有有效数据
                    if (nullStartIndex !== -1) {
                        // 填充之前的空值区间
                        if (method === 'forward') {
                            // 前向填充
                            for (let j = nullStartIndex; j < i; j++) {
                                result[j][tenor] = lastValidValue;
                            }
                        } else if (method === 'linear') {
                            // 线性插值
                            if (lastValidValue !== null) {
                                const nullCount = i - nullStartIndex;
                                const step = (result[i][tenor] - lastValidValue) / (nullCount + 1);
                                for (let j = nullStartIndex; j < i; j++) {
                                    result[j][tenor] = lastValidValue + step * (j - nullStartIndex + 1);
                                }
                            } else {
                                // 没有前值，使用后值
                                for (let j = nullStartIndex; j < i; j++) {
                                    result[j][tenor] = result[i][tenor];
                                }
                            }
                        }
                        nullStartIndex = -1;
                    }
                    lastValidValue = result[i][tenor];
                } else {
                    // 空值
                    if (nullStartIndex === -1) {
                        nullStartIndex = i;
                    }
                }
            }

            // 处理末尾的空值（前向填充）
            if (nullStartIndex !== -1 && method === 'forward') {
                for (let j = nullStartIndex; j < result.length; j++) {
                    result[j][tenor] = lastValidValue;
                }
            }
        });

        return result;
    }

    /**
     * 按期限筛选数据
     * @param {Array} data - 数据数组
     * @param {Array} tenors - 期限数组 (如 ['DGS1', 'DGS10'])
     * @returns {Array} 只包含指定期限的数据
     */
    function filterByTenors(data, tenors) {
        return data.map(row => {
            const filteredRow = { date: row.date };
            tenors.forEach(tenor => {
                filteredRow[tenor] = row[tenor];
            });
            return filteredRow;
        });
    }

    /**
     * 聚合数据
     * @param {Array} data - 原始数据
     * @param {string} type - 聚合类型 ('day', 'week', 'month')
     * @returns {Array} 聚合后的数据
     */
    function aggregateData(data, type) {
        if (type === 'day' || !type) {
            return data;
        }

        // 检查缓存
        if (cache[type]) {
            return cache[type];
        }

        const grouped = {};

        data.forEach(point => {
            const date = new Date(point.date);
            let key;

            if (type === 'week') {
                // 获取周的周一
                const dayOfWeek = date.getDay();
                const weekStart = new Date(date);
                weekStart.setDate(date.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));
                key = weekStart.toISOString().split('T')[0];
            } else if (type === 'month') {
                key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            }

            if (!grouped[key]) {
                grouped[key] = { count: 0, date: key };
                TENORS.forEach(tenor => {
                    grouped[key][tenor] = { sum: 0, validCount: 0 };
                });
            }

            TENORS.forEach(tenor => {
                if (point[tenor] !== null) {
                    grouped[key][tenor].sum += point[tenor];
                    grouped[key][tenor].validCount++;
                }
            });
            grouped[key].count++;
        });

        const aggregated = Object.values(grouped).map(g => {
            const row = { date: g.date };
            TENORS.forEach(tenor => {
                if (g[tenor].validCount > 0) {
                    row[tenor] = g[tenor].sum / g[tenor].validCount;
                } else {
                    row[tenor] = null;
                }
            });
            return row;
        }).sort((a, b) => new Date(a.date) - new Date(b.date));

        // 缓存结果
        cache[type] = aggregated;
        cache.current = type;

        return aggregated;
    }

    /**
     * 按日期范围筛选数据
     * @param {Array} data - 数据数组
     * @param {string} startDate - 开始日期 (YYYY-MM-DD)
     * @param {string} endDate - 结束日期 (YYYY-MM-DD)
     * @returns {Array} 筛选后的数据
     */
    function filterByDateRange(data, startDate, endDate) {
        if (!startDate && !endDate) {
            return data;
        }

        const start = startDate ? new Date(startDate) : new Date('1970-01-01');
        const end = endDate ? new Date(endDate) : new Date();

        return data.filter(point => {
            const pointDate = new Date(point.date);
            return pointDate >= start && pointDate <= end;
        });
    }

    /**
     * 根据时间范围筛选数据
     * @param {Array} data - 数据数组
     * @param {string} range - 时间范围 ('1y', '5y', '10y', 'all')
     * @returns {Array} 筛选后的数据
     */
    function filterByTimeRange(data, range) {
        if (range === 'all') {
            return data;
        }

        const endDate = new Date();
        const startDate = new Date();

        switch (range) {
            case '1y':
                startDate.setFullYear(endDate.getFullYear() - 1);
                break;
            case '5y':
                startDate.setFullYear(endDate.getFullYear() - 5);
                break;
            case '10y':
                startDate.setFullYear(endDate.getFullYear() - 10);
                break;
            default:
                return data;
        }

        return filterByDateRange(data, startDate.toISOString().split('T')[0], endDate.toISOString().split('T')[0]);
    }

    /**
     * 简化的降采样（用于大数据集）
     * 如果数据点超过阈值，则均匀采样
     * @param {Array} data - 数据数组
     * @param {number} threshold - 阈值
     * @returns {Array} 降采样后的数据
     */
    function downsample(data, threshold = 1000) {
        if (data.length <= threshold) {
            return data;
        }

        const step = Math.ceil(data.length / threshold);
        const sampled = [];

        for (let i = 0; i < data.length; i += step) {
            sampled.push(data[i]);
        }

        // 确保最后一个数据点被包含
        const lastIndex = data.length - 1;
        if (sampled[sampled.length - 1] !== data[lastIndex]) {
            sampled.push(data[lastIndex]);
        }

        return sampled;
    }

    /**
     * 获取数据摘要
     * @param {Array} data - 数据数组
     * @returns {Object} 数据摘要
     */
    function getDataSummary(data) {
        if (!data || data.length === 0) {
            return { count: 0, startDate: null, endDate: null };
        }

        return {
            count: data.length,
            startDate: data[0].date,
            endDate: data[data.length - 1].date,
            minDate: data[0].date,
            maxDate: data[data.length - 1].date
        };
    }

    /**
     * 清除缓存
     */
    function clearCache() {
        cache.raw = null;
        cache.day = null;
        cache.week = null;
        cache.month = null;
        cache.current = 'day';
    }

    // 公共 API
    return {
        loadCSVData,
        parseMultiColumnCSV,
        fillMissingValues,
        filterByTenors,
        aggregateData,
        filterByDateRange,
        filterByTimeRange,
        downsample,
        getDataSummary,
        clearCache,
        get TENORS() { return TENORS; },
        get cache() { return cache; }
    };
})();
