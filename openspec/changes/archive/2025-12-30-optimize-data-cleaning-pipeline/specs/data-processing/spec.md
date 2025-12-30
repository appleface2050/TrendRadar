# Delta for Data Processing

## ADDED Requirements

### Requirement: 统一的数据验证机制
系统 MUST 提供统一的数据验证机制，确保数据质量。

#### Scenario: 验证货币供应量数据
- WHEN 处理 M1/M2 数据时
- THEN 系统应自动检查：
  - 日期列是否存在且格式正确
  - 缺失值比例不超过阈值（默认 10%）
  - 无重复日期记录
  - 时间范围符合预期（2016-01-01 之后）

#### Scenario: 检测异常值
- WHEN 数据包含异常值时
- THEN 系统应使用 IQR 方法检测并报告异常值

#### Scenario: 生成质量报告
- WHEN 数据处理完成时
- THEN 系统应生成包含以下信息的质量报告：
  - 处理记录数
  - 缺失值统计
  - 异常值数量
  - 时间范围

### Requirement: 通用数据处理组件
系统 MUST 提供可复用的数据处理组件，减少代码重复。

#### Scenario: 读取 CSV 文件
- WHEN 读取 CSV 文件时
- THEN 系统应自动尝试多种编码（utf-8, utf-8-sig, gbk）
- AND 如果所有编码都失败，应抛出清晰的错误信息

#### Scenario: 标准化日期格式
- WHEN 处理日期列时
- THEN 系统应将日期统一转换为 YYYY-MM-DD 格式
- AND 支持多种输入格式的自动识别

#### Scenario: 保存 CSV 文件
- WHEN 保存 CSV 文件时
- THEN 系统应使用统一的编码（utf-8-sig）
- AND 确保目录存在（自动创建）

### Requirement: 统一的日志记录
系统 MUST 提供统一的日志记录机制，追踪数据处理过程。

#### Scenario: 记录处理步骤
- WHEN 执行数据处理步骤时
- THEN 系统应记录：
  - 步骤名称
  - 开始时间
  - 处理结果（成功/失败）
  - 关键统计信息

#### Scenario: 记录错误和警告
- WHEN 发生错误或警告时
- THEN 系统应记录：
  - 错误类型和消息
  - 发生时间
  - 上下文信息

### Requirement: 单元测试覆盖
系统 MUST 为核心数据处理逻辑提供单元测试。

#### Scenario: 测试数据验证器
- WHEN 运行单元测试时
- THEN DataValidator 的所有方法应有测试覆盖
- AND 包括正常情况和边界情况

#### Scenario: 测试数据处理组件
- WHEN 运行单元测试时
- THEN DataProcessor 的所有方法应有测试覆盖
- AND 使用模拟数据验证输出正确性

### Requirement: 向后兼容性
系统 MUST 保持向后兼容，不影响现有功能。

#### Scenario: 函数接口不变
- WHEN 重构数据处理函数时
- THEN 所有公开函数的输入输出接口保持不变
- AND 调用方无需修改代码

#### Scenario: 数据格式不变
- WHEN 重构数据处理逻辑时
- THEN 生成的 CSV 文件格式保持不变
- AND 数据目录结构保持不变

## MODIFIED Requirements

### Requirement: 代码重复率
系统 MUST 将代码重复率从当前的约 40% 降低到 20% 以下。

#### Scenario: 提取通用逻辑
- WHEN 识别到重复代码模式时
- THEN 应将其提取为可复用的方法
- AND 在所有函数中使用该方法

## REMOVED Requirements
（无）
