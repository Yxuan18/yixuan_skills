#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CNNVD XML 预处理管道：
1. 删除 <PAV>...</PAV> 节点
2. 将新格式转换为旧格式

用法：
    python process_cnnvd.py -f input.xml
    python process_cnnvd.py -f input.xml -o output.xml
"""

import argparse
import sys
from pathlib import Path

from remote_pav import remove_pav
from transform_cnnvd_xml import transform_xml, default_output_path


def process_pipeline(input_path: Path, output_path: Path, xml_version: str = "1.0") -> int:
    """
    执行两步处理管道：
    1. 删除 PAV 节点（中间文件）
    2. 转换格式

    返回: 0=成功, 1=PAV处理失败, 2=格式转换失败
    """
    # 临时中间文件（用于 PAV 处理结果）
    temp_no_pav = input_path.parent / f"{input_path.stem}_no_pav{input_path.suffix}"

    # 步骤1: 删除 PAV 节点
    print(f"[步骤1/2] 删除 <PAV> 节点...")
    if not remove_pav(str(input_path), str(temp_no_pav)):
        return 1

    pav_count = sum(1 for _ in open(input_path, 'rb').read().split(b"<PAV>")) - 1
    print(f"  -> 已删除 {pav_count} 个 <PAV> 节点")

    # 步骤2: 转换格式
    print(f"[步骤2/2] 转换格式...")
    try:
        count = transform_xml(temp_no_pav, output_path, xml_version)
    except Exception as exc:
        print(f"错误: {exc}", file=sys.stderr)
        temp_no_pav.unlink(missing_ok=True)
        return 2

    print(f"  -> 已转换 {count} 个 cnnvd_items 节点")

    # 清理临时文件
    temp_no_pav.unlink(missing_ok=True)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CNNVD XML 预处理管道：删除 <PAV> 节点 + 格式转换"
    )
    parser.add_argument(
        "-f", "--file",
        required=True,
        type=Path,
        help="输入 XML 文件路径"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="输出文件路径（默认: <输入文件名>_old_format.xml）"
    )
    parser.add_argument(
        "--xml-version",
        default="1.0",
        help="旧格式根节点的 cnnvd_xml_version，默认: 1.0"
    )

    args = parser.parse_args()

    input_path = args.file.expanduser().resolve()
    output_path = (
        args.output.expanduser().resolve()
        if args.output
        else default_output_path(input_path)
    )

    # 输入检查
    if not input_path.is_file():
        print(f"错误: 输入文件不存在: {input_path}", file=sys.stderr)
        return 1

    if input_path == output_path:
        print("错误: 输出文件不能与输入文件相同", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 执行管道
    print(f"输入: {input_path}")
    print(f"输出: {output_path}")
    print("-" * 40)

    result = process_pipeline(input_path, output_path, args.xml_version)

    if result == 0:
        output_size = output_path.stat().st_size / 1024 / 1024
        print("-" * 40)
        print(f"完成! 输出文件大小: {output_size:.2f} MB")
        return 0
    else:
        print("-" * 40)
        print("处理失败")
        return result


if __name__ == "__main__":
    sys.exit(main())
