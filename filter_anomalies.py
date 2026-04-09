#!/usr/bin/env python3
"""
基于关键字的条件过滤系统
根据配置文件中的规则过滤异常日志中的冗余内容
"""

import json
import os
from pathlib import Path


def load_filter_config(config_path="filter_config.json"):
    """加载过滤配置"""
    if not os.path.exists(config_path):
        print(f"配置文件 {config_path} 不存在，使用默认配置")
        return {
            "filters": [
                {
                    "keyword": "timestamp",
                    "skip_lines": 1,
                    "description": "跳过时间戳行"
                }
            ]
        }

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def apply_filters(content, filters):
    """应用过滤规则到内容"""
    lines = content.split('\n')
    filtered_lines = []
    skip_counter = 0  # 跳过行计数器
    current_filter_description = None

    for line in lines:
        if skip_counter > 0:
            # 当前处于跳过状态，减少计数器
            skip_counter -= 1
            # 记录被跳过的行数
            if skip_counter == 0 and current_filter_description:
                # 在跳过完成后添加描述信息
                filtered_lines.append(f"[FILTERED: {current_filter_description}]")
            continue

        # 检查是否匹配任何过滤规则
        matched = False
        for rule in filters:
            if rule["keyword"].lower() in line.lower():
                # 匹配到关键字，设置跳过计数器
                skip_counter = rule["skip_lines"]
                current_filter_description = rule["description"]
                matched = True
                break

        if not matched:
            # 不匹配任何过滤规则，保留该行
            filtered_lines.append(line)

    return '\n'.join(filtered_lines)


def filter_anomaly_files(anomalies_dir="anomalies", output_dir="anomalies_filtered"):
    """过滤anomalies目录下的所有异常文件"""
    config = load_filter_config()
    filters = config.get("filters", [])

    if not filters:
        print("没有配置过滤规则，退出")
        return

    print(f"加载了 {len(filters)} 条过滤规则:")
    for i, rule in enumerate(filters, 1):
        print(f"  {i}. 关键字: '{rule['keyword']}', 跳过 {rule['skip_lines']} 行 - {rule['description']}")

    anomalies_path = Path(anomalies_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # 遍历所有子目录（支持 COM-XX/timestamp_name 两层结构）
    processed_files = 0
    for entry in anomalies_path.iterdir():
        if not entry.is_dir():
            continue

        # 判断是否为 COM 口层级目录（不含 anomaly_*.log 文件）
        has_log_files = any(entry.glob("*.log"))
        has_subdirs = any(e.is_dir() for e in entry.iterdir())

        if has_subdirs and not has_log_files:
            # 这是 COM-XX 层级，继续往下一层
            com_dir = entry
            for subdir in com_dir.iterdir():
                if subdir.is_dir():
                    output_subdir = output_path / com_dir.name / subdir.name
                    output_subdir.mkdir(parents=True, exist_ok=True)
                    for log_file in subdir.glob("*.log"):
                        if log_file.name != "anomaly_summary.json":
                            with open(log_file, 'r', encoding='utf-8') as f:
                                original_content = f.read()
                            filtered_content = apply_filters(original_content, filters)
                            output_file = output_subdir / log_file.name
                            with open(output_file, 'w', encoding='utf-8') as f:
                                f.write(filtered_content)
                            print(f"已处理: {log_file} -> {output_file}")
                            processed_files += 1
        else:
            # 这是 timestamp_name 层级（直接在 anomalies/ 下）
            output_subdir = output_path / entry.name
            output_subdir.mkdir(exist_ok=True)
            for log_file in entry.glob("*.log"):
                if log_file.name != "anomaly_summary.json":
                    with open(log_file, 'r', encoding='utf-8') as f:
                        original_content = f.read()
                    filtered_content = apply_filters(original_content, filters)
                    output_file = output_subdir / log_file.name
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(filtered_content)
                    print(f"已处理: {log_file} -> {output_file}")
                    processed_files += 1

    print(f"\n过滤完成! 共处理了 {processed_files} 个文件")
    print(f"结果保存在: {output_dir}/")


def main():
    print("启动基于关键字的条件过滤系统...")
    filter_anomaly_files()


if __name__ == "__main__":
    main()