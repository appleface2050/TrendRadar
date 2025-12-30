# 重构数据获取和导出脚本

## 变更 ID
`refactor-fetch-export-scripts`

## 类型
优化 / 重构

## 动机

### 当前问题
1. **重复的 CSV 保存代码**：每个指标保存都重复相同的模式
   ```python
   output_file = CSV_OUTPUT_DIR / 'us_gdp.csv'
   gdp_data.to_csv(output_file, index=False, encoding='utf-8-sig')
   logger.info(f"✓ 数据已保存: {output_file} ({len(gdp_data)} 条)")
   ```

2. **缺少数据验证**：
   - 没有验证数据质量
   - 没有检查数据完整性
   - 缺少数据统计报告

3. **日志记录不统一**：
   - 使用混合的 logging 模式
   - 没有利用已有的 DataLogger 工具

4. **错误处理不完善**：
   - 部分操作缺少 try-except
   - 错误信息不够详细

### 影响
- 代码维护成本高
- 数据质量问题难以发现
- 日志信息不够结构化

## 目标

### 主要目标
1. 使用 DataProcessor 替代重复的 CSV 保存代码
2. 添加数据验证和质量检查
3. 使用统一的 DataLogger 替代 logging
4. 改进错误处理

### 次要目标
1. 添加单元测试
2. 提高代码可读性

### 非目标
1. 不修改数据获取逻辑（API 调用部分）
2. 不改变输出文件格式和位置

## 提议的解决方案

### 1. 重构 `fetch_and_export_csv.py`
- 使用 DataProcessor 的 `save_csv()` 方法
- 使用 DataLogger 替代 logging
- 添加数据质量检查

### 2. 提取通用的保存逻辑
创建一个辅助方法来处理单个指标的保存：
```python
def save_indicator_data(processor, data, filename, indicator_name):
    """保存指标数据"""
    # 验证数据
    # 保存 CSV
    # 生成质量报告
```

### 3. 添加数据验证
- 检查数据是否为空
- 验证必需列
- 生成质量报告

## 成功标准

### 功能性
- ✅ 所有数据获取功能保持不变
- ✅ CSV 文件格式和位置不变
- ✅ 添加数据质量报告

### 质量性
- ✅ 减少 50% 的代码重复
- ✅ 统一的日志格式
- ✅ 完善的错误处理

### 性能
- ✅ 不显著影响数据获取速度

## 受影响的组件

### 直接修改
- `MacroTrading/scripts/fetch_and_export_csv.py`

### 使用现有工具
- `MacroTrading/utils/data_processor.py`
- `MacroTrading/utils/data_validator.py`
- `MacroTrading/utils/data_logger.py`

## 风险和缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 重构引入 bug | 数据获取失败 | 保留原始文件备份 |
| 输出格式变化 | 影响下游使用 | 对比重构前后的 CSV 文件 |

## 时间估算
- 重构脚本：1-2 小时
- 测试验证：0.5 小时

**总计**：1.5-2.5 小时

## 相关变更
这是继 `optimize-data-cleaning-pipeline` 之后的第二个数据处理优化项目，使用相同的工具库和模式。
