import json
import os
import re
from datetime import datetime

def translate_keywords_in_log(log_file_path, config_file_path, output_dir):
    """
    根据配置文件中的关键词解释规则，将日志文件中的关键词转换为对应的中文解释，
    并生成类似原日志文件的文本格式输出

    参数:
        log_file_path: 输入日志文件路径
        config_file_path: 配置文件路径
        output_dir: 输出目录
    """

    # 读取配置文件
    with open(config_file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 读取日志文件
    with open(log_file_path, 'r', encoding='utf-8') as f:
        log_content = f.read()

    # 按行分割日志内容
    lines = log_content.split('\n')

    # 创建解释后的日志内容
    translated_log_lines = []

    # 遍历每一行
    for line_num, line in enumerate(lines, start=1):
        # 检查这一行是否包含需要解释的关键词
        has_explanation = False
        for item in config['translations']:
            keyword = item['keyword']
            translation = item['translation']  # 仍使用translation字段，但会显示为解释
            category = item['category']

            # 如果当前行包含关键词
            if keyword in line:
                # 添加原始行
                translated_log_lines.append(line.rstrip())

                # 添加解释信息
                translated_log_lines.append(f"  // 解释: {translation} (分类: {category})")

                has_explanation = True
                break  # 避免重复添加同一行的解释

        # 如果该行没有匹配的关键词，则只添加原始行
        if not has_explanation and line.strip():  # 忽略空行
            translated_log_lines.append(line.rstrip())

    # 生成输出文件名（使用 .log 扩展名）
    log_filename = os.path.basename(log_file_path)
    output_filename = f"translated_{log_filename}"
    output_path = os.path.join(output_dir, output_filename)

    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)

    # 写入解释后的日志内容
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(translated_log_lines))

    print(f"解释完成！结果已保存至: {output_path}")

    # 计算解释了多少行
    explanation_count = sum(1 for line in translated_log_lines if line.startswith("  // 解释:"))
    print(f"共解释了 {explanation_count} 个关键行")


def translate_all_logs_in_merged():
    """遍历anomalies_merged下所有子文件夹，对其中的所有日志文件进行解释"""

    base_dir = os.path.dirname(os.path.abspath(__file__))
    merged_dir = os.path.join(base_dir, "anomalies_merged")
    config_file_path = os.path.join(base_dir, "translation_config.json")
    output_base_dir = os.path.join(base_dir, "anomalies_translated")

    # 遍历anomalies_merged下的所有子文件夹
    for subdir in os.listdir(merged_dir):
        subdir_path = os.path.join(merged_dir, subdir)

        # 确保这是一个文件夹
        if os.path.isdir(subdir_path):
            print(f"\n正在处理文件夹: {subdir}")

            # 为该子文件夹创建对应的输出目录
            output_subdir = os.path.join(output_base_dir, subdir)
            os.makedirs(output_subdir, exist_ok=True)

            # 遍历该子文件夹下的所有日志文件
            for file in os.listdir(subdir_path):
                if file.endswith('.log'):
                    log_file_path = os.path.join(subdir_path, file)
                    print(f"  处理文件: {file}")

                    # 对该日志文件进行解释
                    translate_keywords_in_log(log_file_path, config_file_path, output_subdir)


def main():
    # 执行批量解释
    translate_all_logs_in_merged()


if __name__ == "__main__":
    main()