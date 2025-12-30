# Delta for Data Fetch

## ADDED Requirements

### Requirement: 统一的数据保存辅助函数
系统 MUST 提供统一的数据保存辅助函数，消除代码重复。

#### Scenario: 保存单个指标数据
- WHEN 保存指标数据到 CSV 时
- THEN 系统应：
  - 验证数据不为空
  - 生成数据质量报告
  - 使用统一编码保存（utf-8-sig）
  - 记录结构化日志

#### Scenario: 处理保存失败
- WHEN 数据保存失败时
- THEN 系统 SHOULD 记录错误但不中断整个流程

### Requirement: 使用循环处理指标列表
系统 MUST 使用循环处理指标列表，避免重复代码。

#### Scenario: 获取多个美国指标
- WHEN 获取美国宏观数据时
- THEN 系统 SHOULD：
  - 定义指标列表（代码、名称、文件名）
  - 使用循环依次获取
  - 单个指标失败不影响其他指标

### Requirement: 自动数据验证
系统 MUST 在保存数据前自动验证数据质量。

#### Scenario: 验证指标数据
- WHEN 保存指标数据时
- THEN 系统 SHOULD 自动：
  - 检查数据行数
  - 检查列数
  - 检查缺失值
  - 生成质量报告

## MODIFIED Requirements

### Requirement: 代码重复率
数据获取脚本的代码重复率 MUST 从当前的 60% 降低到 5% 以下。

#### Scenario: 提取保存逻辑
- WHEN 识别到重复的保存代码时
- THEN 应将其提取为 `save_indicator_data()` 辅助函数

### Requirement: 错误处理
错误处理 MUST 从部分覆盖改进到全覆盖。

#### Scenario: 单个指标失败
- WHEN 某个指标获取失败时
- THEN 系统 SHOULD：
  - 记录详细错误信息
  - 继续处理下一个指标
  - 在总结中报告失败项

## REMOVED Requirements
（无）
