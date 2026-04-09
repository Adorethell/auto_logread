#!/usr/bin/env python3
"""
日志异常提取程序
从嵌入式模块日志中提取包含'offline'关键字的段落，
以'kplv ack'标记作为边界。
"""

import os
import re
import json
import logging
import sys
from typing import List, Tuple, Optional
from pathlib import Path


class LogReader:
    """用于高效读取大日志文件的模块。"""

    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path

    def read_log_lines(self) -> List[str]:
        """逐行读取日志文件以避免内存溢出。"""
        lines = []
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    lines.append(line.rstrip('\n\r'))
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试使用其他编码
            with open(self.log_file_path, 'r', encoding='latin-1') as f:
                for line_num, line in enumerate(f, start=1):
                    lines.append(line.rstrip('\n\r'))

        return lines


class AnomalyDetector:
    """用于检测日志数据中异常段的模块。"""

    def __init__(self, log_lines: List[str], exclude_keywords: List[str] = None, exclude_patterns: List[str] = None):
        self.log_lines = log_lines
        self.exclude_keywords = exclude_keywords or []
        self.exclude_patterns = [re.compile(p) for p in (exclude_patterns or [])]
        self.offline_positions = []
        self.kplv_ack_positions = []
        self._index_positions()

    def _is_excluded(self, line: str) -> bool:
        """判断行是否命中排除规则。"""
        if any(kw in line for kw in self.exclude_keywords):
            return True
        if any(p.search(line) for p in self.exclude_patterns):
            return True
        return False

    def _index_positions(self):
        """索引'offline'和'kplv ack'出现的位置。"""
        for idx, line in enumerate(self.log_lines):
            if 'offline' in line:
                if not self._is_excluded(line):
                    self.offline_positions.append(idx)
            if 'kplv ack' in line:
                self.kplv_ack_positions.append(idx)

    def find_segments(self) -> List[Tuple[int, int]]:
        """查找包含'offline'且以'kplv ack'为边界的段落。"""
        segments = []

        for offline_pos in self.offline_positions:
            # 查找之前的'kplv ack'位置
            start_pos = None
            for kplv_pos in reversed(self.kplv_ack_positions):
                if kplv_pos < offline_pos:
                    start_pos = kplv_pos
                    break

            # 查找下一个'kplv ack'位置
            end_pos = None
            for kplv_pos in self.kplv_ack_positions:
                if kplv_pos > offline_pos:
                    end_pos = kplv_pos
                    break

            # 如果找到两个边界，则添加段落
            if start_pos is not None and end_pos is not None:
                segments.append((start_pos, end_pos))
            elif start_pos is not None and end_pos is None:
                # 处理offline后没有kplv ack的情况
                segments.append((start_pos, len(self.log_lines)-1))
            elif start_pos is None and end_pos is not None:
                # 处理offline前没有kplv ack的情况
                segments.append((0, end_pos))

        # 去除重复项同时保持顺序
        unique_segments = []
        seen = set()
        for segment in segments:
            if segment not in seen:
                unique_segments.append(segment)
                seen.add(segment)

        return unique_segments


class ResultExporter:
    """用于导出异常结果的模块。"""

    def __init__(self, output_dir: str = "anomalies"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export_segments(self, log_lines: List[str], segments: List[Tuple[int, int]], input_file_name: str = "test.log"):
        """将识别的段落导出到单独的文件中。"""
        anomaly_files = []

        for idx, (start, end) in enumerate(segments):
            # 定义带行号的文件名
            anomaly_filename = f"anomaly_{start}_{end}.log"
            anomaly_path = self.output_dir / anomaly_filename

            # 提取段落内容
            segment_content = "\n".join(log_lines[start:end+1])

            # 写入文件
            with open(anomaly_path, 'w', encoding='utf-8') as f:
                f.write(segment_content)

            anomaly_files.append({
                'filename': anomaly_filename,
                'start_line': start,
                'end_line': end,
                'line_count': end - start + 1,
                'input_file': input_file_name
            })

        # 创建汇总/索引文件
        self._create_summary(anomaly_files, input_file_name)

        return anomaly_files

    def _create_summary(self, anomaly_files: List[dict], input_file_name: str):
        """创建列明所有异常的汇总文件。"""
        summary_path = self.output_dir / "anomaly_summary.json"

        summary_data = {
            'input_file': input_file_name,
            'total_anomalies': len(anomaly_files),
            'anomalies': anomaly_files
        }

        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)


def select_log_file(interactive=True, config=None) -> List[str]:
    """交互式或自动选择要分析的日志文件。"""
    # 从配置获取日志目录，如果配置未提供或无效，则使用默认值
    if config and "input_file" in config:
        input_path = Path(config["input_file"])
        if input_path.is_dir():
            # 如果是目录，使用该目录
            logs_dir = input_path
        else:
            # 如果是文件，使用其父目录
            logs_dir = input_path.parent
    else:
        logs_dir = Path("logs")

    if not logs_dir.exists():
        print(f"错误：日志目录'{logs_dir}'不存在。")
        return []

    # 获取目录中的所有日志文件（包括子目录）
    log_files = list(logs_dir.rglob("*.log")) + list(logs_dir.rglob("*.txt"))

    if not log_files:
        print(f"在'{logs_dir}'目录中未找到日志文件。")
        return []

    print("\n可用的日志文件：")
    for i, log_file in enumerate(log_files, 1):
        print(f"  {i}. {log_file.name}")

    print(f"  {len(log_files) + 1}. 所有文件")
    print(f"  {len(log_files) + 2}. 退出")

    if not interactive:
        # 在非交互模式下，分析所有文件
        print(f"\n自动分析所有文件（非交互模式）...")
        return [str(log_file) for log_file in log_files]

    try:
        choice = int(input(f"\n输入您的选择 (1-{len(log_files) + 2}): "))

        if choice < 1 or choice > len(log_files) + 2:
            print("无效选择。请重试。")
            return select_log_file(interactive)

        if choice == len(log_files) + 1:  # 所有文件
            return [str(log_file) for log_file in log_files]
        elif choice == len(log_files) + 2:  # 退出
            print("退出...")
            sys.exit(0)
        else:
            # 选择了单个文件
            return [str(log_files[choice - 1])]

    except ValueError:
        print("无效输入。请输入数字。")
        return select_log_file(interactive)
    except (EOFError, KeyboardInterrupt):
        print("\n无法进行交互输入。自动分析所有文件...")
        return [str(log_file) for log_file in log_files]


def main():
    """主要执行函数。"""
    # 加载配置
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        # 默认配置
        config = {
            "input_file": "logs/test.log",
            "output_dir": "anomalies",
            "search_keyword": "offline",
            "boundary_keyword": "kplv ack"
        }

    # 确定是否以交互模式运行
    import sys
    interactive = sys.stdin.isatty() and sys.stdout.isatty()

    # 获取要分析的文件列表
    files_to_analyze = select_log_file(interactive, config)

    if not files_to_analyze:
        return

    output_dir = config.get("output_dir", "anomalies")

    # 处理每个选定的文件
    for input_file in files_to_analyze:
        # 根据日志文件名为本次分析创建子目录
        input_path = Path(input_file)
        log_filename = input_path.stem
        subfolder_name = log_filename

        # 如果日志文件在子目录下（如 COM-XX），则在输出目录中保持该层级
        parent_name = input_path.parent.name
        logs_dir = Path(config.get("input_file", "logs"))
        if not logs_dir.is_dir():
            logs_dir = logs_dir.parent
        # 父目录不是 logs 根目录时，说明文件在子文件夹（COM 口）下
        if parent_name and parent_name != logs_dir.name and parent_name != str(logs_dir):
            output_subdir = Path(output_dir) / parent_name / subfolder_name
        else:
            output_subdir = Path(output_dir) / subfolder_name

        print(f"\n开始对文件进行日志分析: {input_file}")

        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            print(f"错误：输入文件'{input_file}'不存在。")
            continue

        # 创建输出子目录
        output_subdir.mkdir(parents=True, exist_ok=True)

        try:
            # 读取日志文件
            reader = LogReader(input_file)
            log_lines = reader.read_log_lines()
            print(f"成功从日志文件读取 {len(log_lines)} 行")

            # 检测异常
            exclude_keywords = config.get("exclude_keywords", [])
            exclude_patterns = config.get("exclude_patterns", [])
            detector = AnomalyDetector(log_lines, exclude_keywords, exclude_patterns)
            segments = detector.find_segments()
            print(f"发现 {len(segments)} 个异常段")

            # 将结果导出到子目录
            exporter = ResultExporter(str(output_subdir))
            anomaly_files = exporter.export_segments(log_lines, segments, os.path.basename(input_file))

            print(f"分析完成。找到 {len(segments)} 个唯一异常段。")
            print(f"结果保存到 '{output_subdir}' 目录:")
            for anomaly in anomaly_files:
                print(f"  - {anomaly['filename']} ({anomaly['line_count']} 行)")

        except Exception as e:
            print(f"分析 {input_file} 时出错: {str(e)}")
            logging.exception("日志分析错误")

    print(f"\n所有选定的文件都已处理完毕。")


if __name__ == "__main__":
    main()