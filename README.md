# 日志异常提取与分析系统

## 项目概述

这是一个专门针对嵌入式模块日志文件进行分析的自动化工具，主要用于识别和提取包含"miio_offline_hook_default"关键字的异常段落。系统能够根据配置灵活地定义搜索关键字和边界关键字，并提供完整的日志分析、过滤和翻译功能。

## 功能特性

- **异常段落识别**：从日志文件中识别包含"miio_offline_hook_default"关键字的异常段落
- **智能边界检测**：以"**kplv ack**"作为异常段落的上下边界
- **批量文件处理**：支持单个文件、多文件或全部文件的选择性处理
- **自动化分析流程**：提供一键式自动化处理脚本
- **数据过滤优化**：根据配置过滤冗余内容，提升分析质量
- **过滤标记合并**：将连续相同的过滤标记进行合并展示
- **关键词翻译解释**：为技术术语提供中文解释，便于理解
- **时间戳目录管理**：每次分析结果保存在带时间戳的独立子目录中

## 文件结构

```
auto_logread_v2/
├── log_analyzer.py         # 主程序：日志异常提取核心逻辑
├── filter_anomalies.py     # 过滤模块：基于关键字的条件过滤
├── merge_filtered.py       # 合并模块：过滤标记合并
├── translate_log.py        # 翻译模块：关键词翻译解释
├── auto_process.py         # 自动化脚本：一键执行完整流程
├── config.json             # 主配置文件
├── filter_config.json      # 过滤规则配置文件
├── merge_config.json       # 合并规则配置文件
├── translation_config.json # 翻译映射配置文件
├── logs/                   # 日志文件存放目录
│   ├── test.log
│   └── test copy.log
├── anomalies/              # 原始异常段落输出目录
├── anomalies_filtered/     # 过滤后的异常数据目录
├── anomalies_merged/       # 合并过滤标记后的异常数据目录
└── anomalies_translated/   # 添加关键词解释的日志文件目录
```

## 核心组件说明

### 1. log_analyzer.py (主分析器)
- **LogReader类**：高效读取大日志文件，支持多种编码格式
- **AnomalyDetector类**：检测包含配置搜索关键字（默认"miio_offline_hook_default"）的异常段，以"kplv ack"为边界
- **ResultExporter类**：导出识别的异常段落到独立文件
- 支持交互式选择日志文件，可选择单个、多个或全部文件处理
- 结果保存在按时间戳命名的子目录中

### 2. filter_anomalies.py (过滤器)
- 基于关键字的条件过滤系统
- 根据配置文件`filter_config.json`中的规则过滤冗余内容
- 可跳过指定行数的无关内容，并添加过滤标记

### 3. merge_filtered.py (合并器)
- 将连续相同的过滤标记进行合并
- 减少重复的过滤标记，提高日志可读性
- 根据正则表达式匹配和合并标记

### 4. translate_log.py (翻译器)
- 为日志中的技术术语添加中文解释
- 根据`translation_config.json`配置映射关系
- 输出带有注释解释的增强型日志文件

### 5. auto_process.py (自动化脚本)
- 一键执行完整的日志分析流程
- 按顺序执行：分析 → 过滤 → 合并 → 翻译
- 提供友好的用户界面和进度反馈

## 配置文件详解

### config.json (主配置)
```json
{
  "input_file": "logs/test.log",    // 输入日志文件路径
  "output_dir": "anomalies",        // 输出目录
  "search_keyword": "miio_offline_hook_default",  // 搜索的关键字
  "boundary_keyword": "kplv ack"    // 边界关键字
}
```

### filter_config.json (过滤配置)
```json
{
  "filters": [
    {
      "keyword": "wapi_scan_stat",          // 要过滤的关键词
      "skip_lines": 5,                      // 跳过行数
      "description": "跳过wapi_scan_stat行" // 描述信息
    }
  ]
}
```

### merge_config.json (合并配置)
```json
{
  "merges": [
    {
      "pattern": "\\[FILTERED: 跳过wapi_scan_stat行\\]", // 匹配模式（正则）
      "output": "\n[FILTERED: wapi_scan_stats搜索wifi过程略...]\n", // 合并后输出
      "description": "合并wapi_scan_stat过滤标记"
    }
  ]
}
```

### translation_config.json (翻译配置)
```json
{
  "translations": [
    {
      "keyword": "Wi-Fi station link down",           // 关键词
      "translation": "Wi-Fi连接断开 - 设备与无线网络断开连接", // 中文解释
      "category": "network"                           // 分类
    }
  ]
}
```

## 使用方法

### 方法一：交互式运行
```bash
python log_analyzer.py
```
- 程序会列出`logs/`目录下的所有日志文件
- 可选择单个文件、所有文件或退出程序
- 适用于手动选择特定文件进行分析

### 方法二：一键自动化处理
```bash
python auto_process.py
```
- 自动执行完整的处理流程（分析 → 过滤 → 合并 → 翻译）
- 提供文件选择界面
- 显示每个步骤的进度和结果

### 方法三：分步处理
```bash
# 1. 运行日志分析
python log_analyzer.py

# 2. 运行异常数据过滤
python filter_anomalies.py

# 3. 运行过滤标记合并
python merge_filtered.py

# 4. 运行关键词翻译解释
python translate_log.py
```

## 输出说明

处理完成后，会在以下目录中生成相应文件：

- `anomalies/YYYYMMDD_HHMMSS_filename/`：包含原始异常段落
- `anomalies_filtered/YYYYMMDD_HHMMSS_filename/`：包含过滤后的异常数据
- `anomalies_merged/YYYYMMDD_HHMMSS_filename/`：包含合并标记后的数据
- `anomalies_translated/YYYYMMDD_HHMMSS_filename/`：包含添加解释的增强日志

## 适用场景

- 嵌入式系统日志分析
- IoT设备离线问题排查
- 网络连接异常检测
- 大规模日志文件批处理
- 技术日志的快速解读

## 注意事项

- 日志文件应存放在`logs/`目录下
- 确保配置文件格式正确
- 大文件处理可能需要较长时间
- 可根据实际需求修改配置文件中的关键词和规则