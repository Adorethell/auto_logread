# CLAUDE 使用指南

本项目使用 Claude Code 进行开发和维护。以下是关于如何与 Claude 交互以及项目的特定配置说明。

## 语言设置

为了确保沟通顺畅，Claude 在此项目中将始终使用中文进行回答。
当运行log_analysis的skill时，不编写任何python代码，只输出Claude的分析结果。

## 项目概述

这是一个日志异常段落提取程序，旨在从嵌入式模组的日志文件中识别包含"miio_offline_hook_default"关键字的异常段落。

### 主要功能

- 从日志文件中识别包含"miio_offline_hook_default"关键字的异常
- 以"kplv ack"作为异常段落的上下边界
- 将识别出的异常段落保存到独立文件
- 支持异常段落合并功能
- 在运行时交互式显示可选的日志文件，并让用户选择要分析的文件或全部文件
- 将每次分析结果保存在anomalies目录下的时间戳子文件夹中
- 提供基于关键字的条件过滤功能，可根据配置删除指定行数的内容
- 提供过滤标记合并功能，将连续的相同过滤标记合并为一条描述

### 文件结构

- `log_analyzer.py` - 主程序文件
- `filter_anomalies.py` - 基于关键字的异常数据过滤脚本
- `merge_filtered.py` - 过滤标记合并脚本
- `filter_config.json` - 过滤规则配置文件
- `merge_config.json` - 合并规则配置文件
- `config.json` - 日志分析配置文件
- `logs/` - 日志文件存放目录
- `anomalies/` - 异常段落输出主目录
  - `YYYYMMDD_HHMMSS_filename/` - 包含特定分析结果的子文件夹
- `anomalies_filtered/` - 过滤后的异常数据目录
- `anomalies_merged/` - 合并过滤标记后的异常数据目录

### 使用方法

运行程序时无需指定参数，程序会自动列出logs目录下的所有日志文件，您可以：
- 选择单个文件进行分析
- 选择分析所有文件
- 退出程序

在自动化环境中，程序会自动分析所有日志文件。

首先运行以下命令过滤异常数据：
```bash
python filter_anomalies.py
```

然后运行以下命令合并过滤标记：
```bash
python merge_filtered.py
```

## Claude 工作流程

1. 分析需求和代码变更请求
2. 根据项目架构提供解决方案
3. 使用中文与开发者交流
4. 维护代码质量和项目一致性

## 特殊指令

- 所有回复必须使用中文
- 优先考虑现有代码结构和风格
- 修改代码前先阅读相关文件
- 遵循项目中既定的编程模式