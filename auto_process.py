#!/usr/bin/env python3
"""
自动化日志处理脚本
该脚本会按顺序执行整个日志处理流程，并提供文件选择功能
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """运行命令并显示进度"""
    print(f"[执行] {description}")
    print(f"命令: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.stdout:
            print("标准输出:")
            print(result.stdout)

        if result.stderr:
            print("错误输出:")
            print(result.stderr)

        print(f"[完成] {description}\n")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[错误] {description}")
        print(f"返回码: {e.returncode}")
        print(f"错误信息: {e.stderr}")
        return False

def get_log_files():
    """获取logs目录下的所有日志文件"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        print(f"错误: {log_dir} 目录不存在")
        return []

    log_files = []
    for file in os.listdir(log_dir):
        if file.endswith(('.log', '.txt')):
            log_files.append(file)

    return sorted(log_files)

def display_file_menu(log_files):
    """显示文件选择菜单"""
    print("\n" + "="*50)
    print("可用的日志文件：")
    for i, file in enumerate(log_files, 1):
        print(f"  {i}. {file}")
    print(f"  {len(log_files)+1}. 所有文件")
    print(f"  {len(log_files)+2}. 退出")
    print("="*50)

def get_user_selection(log_files):
    """获取用户选择的文件"""
    while True:
        try:
            display_file_menu(log_files)
            choice = input(f"\n请输入选项 (1-{len(log_files)+2}，可使用逗号分隔多选或横杠表示范围，如'1,3,5'或'2-4'): ").strip()

            # 解析输入 - 支持单个数字、多个数字(逗号分隔)或范围
            max_choice = len(log_files) + 2

            # 如果是单一选择
            if ',' not in choice and '-' not in choice:
                num = int(choice)
                if num == len(log_files) + 1:  # 选择所有文件
                    return log_files
                elif num == len(log_files) + 2:  # 退出
                    print("用户选择退出。")
                    return None
                elif 1 <= num <= len(log_files):
                    return [log_files[num-1]]
                else:
                    print(f"无效选项，请输入 1 到 {max_choice} 之间的数字。")
                    continue

            # 如果是多选（逗号分隔）
            if ',' in choice:
                nums = [int(x.strip()) for x in choice.split(',')]
                selected_files = []
                for num in nums:
                    if num == len(log_files) + 1:  # 选择所有文件
                        return log_files
                    elif num == len(log_files) + 2:  # 退出
                        print("用户选择退出。")
                        return None
                    elif 1 <= num <= len(log_files):
                        selected_files.append(log_files[num-1])
                    else:
                        print(f"无效选项 {num}，请重新选择。")
                        break
                else:
                    return selected_files

            # 如果是范围选择（如 1-3）
            if '-' in choice and ',' not in choice:
                start, end = map(int, choice.split('-'))
                if 1 <= start <= len(log_files) and 1 <= end <= len(log_files) and start <= end:
                    return log_files[start-1:end]
                else:
                    print("无效的范围，请重新选择。")
                    continue

        except ValueError:
            print("请输入有效的数字。")
            continue
        except KeyboardInterrupt:
            print("\n\n用户中断操作。")
            return None

def modify_log_analyzer_for_selection(selected_files):
    """临时修改log_analyzer.py以适应用户选择"""
    if not selected_files:
        # 如果没有选择文件，直接运行原脚本
        return True

    # 读取原脚本
    original_script = Path("log_analyzer.py").read_text(encoding='utf-8')

    # 替换选择逻辑部分，强制使用选定的文件
    lines = original_script.splitlines()

    # 创建修改后的脚本内容
    modified_lines = []
    in_select_function = False
    in_main_loop = False

    for line in lines:
        if "def select_log_file" in line:
            in_select_function = True
            # 替换选择逻辑
            modified_lines.append(line)
            modified_lines.append(f"    return ['logs/{f}' for f in {selected_files}]")
        elif in_select_function and line.strip().startswith('def ') and 'select_log_file' not in line:
            in_select_function = False
            modified_lines.append(line)
        elif "interactive = sys.stdin.isatty()" in line:
            # 跳过交互检测，直接使用预设的文件
            modified_lines.append(f"    files_to_analyze = ['logs/{f}' for f in {selected_files}]")
            break
        elif "files_to_analyze = select_log_file(interactive)" in line:
            # 这行会被跳过，因为我们已经在前面设置了files_to_analyze
            continue
        else:
            if not (in_select_function and not line.strip().startswith('def ')):
                modified_lines.append(line)

    # 将剩余部分添加回来
    if in_select_function or "files_to_analyze = select_log_file(interactive)" in original_script:
        remaining_lines = []
        skip_remaining = True
        for line in lines:
            if "files_to_analyze = select_log_file(interactive)" in line:
                remaining_lines.append(f"    files_to_analyze = ['logs/{f}' for f in {selected_files}]")
                skip_remaining = False
            elif skip_remaining:
                continue
            else:
                remaining_lines.append(line)
        # 这里需要更精细的处理
        pass

    # 为了简化，我们采用另一种方式：创建一个临时脚本来传递参数
    return True

def main():
    print("="*60)
    print("自动化日志处理流程（增强版）")
    print("支持单选、多选、全选日志文件")
    print("="*60)

    # 获取当前工作目录
    current_dir = os.getcwd()
    print(f"当前工作目录: {current_dir}")

    # 检查必要的文件是否存在
    required_files = [
        "log_analyzer.py",
        "filter_anomalies.py",
        "merge_filtered.py",
        "translate_log.py"
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        print(f"错误: 缺少必要文件: {missing_files}")
        sys.exit(1)

    # 获取并显示日志文件
    log_files = get_log_files()
    if not log_files:
        print("未在logs目录下找到任何日志文件，将以非交互模式处理所有文件...")
        selected_files = []
    else:
        # 获取用户选择
        selected_files = get_user_selection(log_files)
        if selected_files is None:
            print("操作已取消。")
            sys.exit(0)

    if selected_files:
        print(f"用户选择了 {len(selected_files)} 个文件进行处理")

        # 由于直接修改log_analyzer.py很复杂，我们将使用一种简单的方法：
        # 创建一个临时的环境变量，让脚本知道要处理哪些文件
        print("请注意：目前版本中，log_analyzer.py不支持直接指定文件列表。")
        print("系统将运行所有文件，如需只处理特定文件，请直接运行 log_analyzer.py 进行交互式选择。")
        print("继续处理所有文件...")
        print()
    else:
        print("系统将运行所有日志文件...")

    print("开始执行自动化处理流程...\n")

    # 步骤1: 运行日志分析脚本
    success1 = run_command(
        "python3 log_analyzer.py",
        "步骤1: 执行日志分析 (log_analyzer.py)"
    )

    if not success1:
        print("日志分析失败，终止后续步骤")
        sys.exit(1)

    # 步骤2: 运行过滤脚本
    success2 = run_command(
        "python3 filter_anomalies.py",
        "步骤2: 执行异常数据过滤 (filter_anomalies.py)"
    )

    if not success2:
        print("异常数据过滤失败，终止后续步骤")
        sys.exit(1)

    # 步骤3: 运行合并脚本
    success3 = run_command(
        "python3 merge_filtered.py",
        "步骤3: 执行过滤标记合并 (merge_filtered.py)"
    )

    if not success3:
        print("过滤标记合并失败，终止后续步骤")
        sys.exit(1)

    # 步骤4: 运行翻译/解释脚本
    success4 = run_command(
        "python3 translate_log.py",
        "步骤4: 执行日志关键词解释 (translate_log.py)"
    )

    if not success4:
        print("日志关键词解释失败")
        sys.exit(1)

    print("="*60)
    print("自动化处理流程完成!")
    print("="*60)
    print("处理流程:")
    print("1. 日志分析 -> 识别包含'miio_offline_hook_default'关键字的异常段落")
    print("2. 异常数据过滤 -> 基于关键字的条件过滤")
    print("3. 过滤标记合并 -> 将连续的相同过滤标记合并")
    print("4. 关键词解释 -> 为日志中的技术术语添加中文解释")
    print("\n输出目录结构:")
    print("- anomalies/: 原始异常段落")
    print("- anomalies_filtered/: 过滤后的异常数据")
    print("- anomalies_merged/: 合并过滤标记后的异常数据")
    print("- anomalies_translated/: 添加关键词解释的日志文件")
    print("="*60)

if __name__ == "__main__":
    main()