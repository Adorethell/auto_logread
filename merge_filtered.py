#!/usr/bin/env python3
"""
过滤标记合并脚本
将anomalies_filtered目录下的文件中连续相同的过滤标记进行合并
"""

import json
import os
from pathlib import Path
import re


def load_merge_config(config_path="merge_config.json"):
    """加载合并配置"""
    if not os.path.exists(config_path):
        print(f"配置文件 {config_path} 不存在，使用默认配置")
        return {
            "merges": [
                {
                    "pattern": r"\\[FILTERED: 跳过wapi_scan_stat行\\]",
                    "output": "[FILTERED: 多个wapi_scan_stat行已被跳过]",
                    "description": "合并wapi_scan_stat过滤标记"
                },
                {
                    "pattern": r"\\[FILTERED: 跳过bl616_wifi_sta_scan行\\]",
                    "output": "[FILTERED: 多个bl616_wifi_sta_scan行已被跳过]",
                    "description": "合并bl616_wifi_sta_scan过滤标记"
                }
            ]
        }

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_consecutive_lines(content, merges):
    """合并连续的过滤标记行"""
    lines = content.split('\n')
    merged_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # 检查是否匹配任何合并规则
        merged = False
        for rule in merges:
            pattern = rule["pattern"]
            compiled_pattern = re.compile(pattern)

            # 检查当前行是否匹配模式
            if compiled_pattern.search(line):
                # 计算连续匹配的数量
                count = 1
                j = i + 1
                while j < len(lines) and compiled_pattern.search(lines[j]):
                    count += 1
                    j += 1

                # 如果有连续匹配（至少2个），则合并
                if count >= 2:
                    merged_lines.append(rule["output"])
                    i = j  # 跳过所有连续匹配的行
                    merged = True
                    break

        if not merged:
            merged_lines.append(line)
            i += 1

    return '\n'.join(merged_lines)


def merge_filtered_files(input_dir="anomalies_filtered", output_dir="anomalies_merged"):
    """合并anomalies_filtered目录下的所有文件中的连续过滤标记"""
    config = load_merge_config()
    merges = config.get("merges", [])

    if not merges:
        print("没有配置合并规则，退出")
        return

    print(f"加载了 {len(merges)} 条合并规则:")
    for i, rule in enumerate(merges, 1):
        print(f"  {i}. 模式: '{rule['pattern']}' -> 输出: '{rule['output']}' - {rule['description']}")

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # 遍历所有子目录
    processed_files = 0
    for subdir in input_path.iterdir():
        if subdir.is_dir():
            # 为每个子目录创建对应的输出子目录
            output_subdir = output_path / subdir.name
            output_subdir.mkdir(exist_ok=True)

            # 处理该子目录中的所有.log文件
            for log_file in subdir.glob("*.log"):
                if log_file.name != "anomaly_summary.json":  # 排除摘要文件
                    # 读取原始内容
                    with open(log_file, 'r', encoding='utf-8') as f:
                        original_content = f.read()

                    # 应用合并规则
                    merged_content = merge_consecutive_lines(original_content, merges)

                    # 保存合并后的内容
                    output_file = output_subdir / log_file.name
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(merged_content)

                    print(f"已处理: {log_file} -> {output_file}")
                    processed_files += 1

    print(f"\n合并完成! 共处理了 {processed_files} 个文件")
    print(f"结果保存在: {output_dir}/")


def main():
    print("启动过滤标记合并脚本...")
    merge_filtered_files()


if __name__ == "__main__":
    main()