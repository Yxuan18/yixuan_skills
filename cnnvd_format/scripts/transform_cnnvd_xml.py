#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
将 CNNVD 新格式 XML 转换为旧格式。

转换规则（新 -> 旧）：
    cnnvd_items                         -> entry
    cnnvd_id                            -> vuln-id
    cve_id                              -> other-id/cve-id
    severity/overallseverity            -> severity
    vuln_type                           -> vuln-type
    vuln_descript                       -> vuln-descript

根节点：
    <cnnvd publisher="..." date="2026-07-27" date_range="..." format="...">
转换为：
    <cnnvd cnnvd_xml_version="1.0" pub_date="2026-07-27">

用法：
    python cnnvd_new_to_old.py -f input.xml
    python cnnvd_new_to_old.py -f input.xml -o output.xml
    python cnnvd_new_to_old.py -f input.xml --xml-version 1.0

未指定 -o 时，默认输出：
    input_old_format.xml
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


def split_tag(tag: str) -> tuple[str, str]:
    """返回 XML 标签的命名空间和本地名称。"""
    if tag.startswith("{") and "}" in tag:
        namespace, name = tag[1:].split("}", 1)
        return namespace, name
    return "", tag


def local_name(tag: str) -> str:
    """取得不含命名空间的标签名。"""
    return split_tag(tag)[1]


def make_tag(reference_tag: str, name: str) -> str:
    """使用参考标签的命名空间创建新标签。"""
    namespace, _ = split_tag(reference_tag)
    return f"{{{namespace}}}{name}" if namespace else name


def find_direct_child(parent: ET.Element, name: str) -> Optional[ET.Element]:
    """按本地名称查找直接子节点。"""
    for child in parent:
        if local_name(child.tag) == name:
            return child
    return None


def rename_direct_children(parent: ET.Element, old_name: str, new_name: str) -> None:
    """重命名指定的直接子节点。"""
    for child in parent:
        if local_name(child.tag) == old_name:
            child.tag = make_tag(child.tag, new_name)


def convert_cve_id(item: ET.Element) -> None:
    """
    将：
        <cve_id>CVE-XXXX-XXXX</cve_id>
    转换为：
        <other-id>
          <cve-id>CVE-XXXX-XXXX</cve-id>
          <bugtraq-id />
        </other-id>
    """
    for index, child in enumerate(list(item)):
        if local_name(child.tag) != "cve_id":
            continue

        other_id = ET.Element(make_tag(child.tag, "other-id"))
        other_id.tail = child.tail

        cve_id = ET.SubElement(other_id, make_tag(child.tag, "cve-id"))
        cve_id.text = child.text

        ET.SubElement(other_id, make_tag(child.tag, "bugtraq-id"))

        item.remove(child)
        item.insert(index, other_id)


def convert_severity(item: ET.Element) -> None:
    """
    将：
        <severity>
          <technicalseverity>高危</technicalseverity>
          <overallseverity>高危</overallseverity>
        </severity>
    转换为：
        <severity>高危</severity>

    优先使用 overallseverity；若不存在，则使用 technicalseverity；
    如果 severity 本身已经是纯文本，则保留原文本。
    """
    for severity in item:
        if local_name(severity.tag) != "severity":
            continue

        overall = find_direct_child(severity, "overallseverity")
        technical = find_direct_child(severity, "technicalseverity")

        if overall is not None:
            value = overall.text
        elif technical is not None:
            value = technical.text
        else:
            value = severity.text

        for child in list(severity):
            severity.remove(child)

        severity.text = value


def convert_item(item: ET.Element) -> None:
    """转换单个 cnnvd_items 节点。"""
    item.tag = make_tag(item.tag, "entry")

    rename_direct_children(item, "cnnvd_id", "vuln-id")
    convert_cve_id(item)
    convert_severity(item)
    rename_direct_children(item, "vuln_type", "vuln-type")
    rename_direct_children(item, "vuln_descript", "vuln-descript")


def convert_root(root: ET.Element, xml_version: str) -> None:
    """转换 cnnvd 根节点属性。"""
    if local_name(root.tag) != "cnnvd":
        raise ValueError(f"根节点应为 <cnnvd>，实际为 <{local_name(root.tag)}>")

    pub_date = root.attrib.get("date", root.attrib.get("pub_date", ""))

    # 旧格式只保留这两个属性。
    root.attrib.clear()
    root.set("cnnvd_xml_version", xml_version)
    root.set("pub_date", pub_date)


def transform_xml(input_path: Path, output_path: Path, xml_version: str) -> int:
    """转换 XML，返回已处理的 cnnvd_items 数量。"""
    # Python 3.14+ 已默认禁用外部实体，无需 resolve_entities 参数
    # 保留 insert_comments=True 以保留原始 XML 中的注释
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    tree = ET.parse(input_path, parser=parser)
    root = tree.getroot()

    convert_root(root, xml_version)

    items = [
        element
        for element in root.iter()
        if isinstance(element.tag, str) and local_name(element.tag) == "cnnvd_items"
    ]

    for item in items:
        convert_item(item)

    try:
        ET.indent(tree, space="  ")
    except AttributeError:
        pass

    tree.write(
        output_path,
        encoding="UTF-8",
        xml_declaration=True,
        short_empty_elements=True,
    )

    return len(items)


def default_output_path(input_path: Path) -> Path:
    """生成默认输出文件路径。"""
    suffix = input_path.suffix or ".xml"
    return input_path.with_name(f"{input_path.stem}_old_format{suffix}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将 CNNVD 新格式 XML 转换为旧格式。"
    )
    parser.add_argument(
        "-f",
        "--file",
        required=True,
        type=Path,
        help="需要处理的新格式 XML 文件",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="输出文件；未指定时自动生成 *_old_format.xml",
    )
    parser.add_argument(
        "--xml-version",
        default="1.0",
        help="旧格式根节点的 cnnvd_xml_version，默认：1.0",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_path = args.file.expanduser().resolve()
    output_path = (
        args.output.expanduser().resolve()
        if args.output
        else default_output_path(input_path)
    )

    if not input_path.is_file():
        print(f"错误：输入文件不存在或不是普通文件：{input_path}", file=sys.stderr)
        return 1

    if input_path == output_path:
        print("错误：输出文件不能与输入文件相同。", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        count = transform_xml(input_path, output_path, args.xml_version)
    except ET.ParseError as exc:
        print(f"错误：XML 解析失败：{exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 3

    print(f"转换完成：共处理 {count} 个 cnnvd_items 节点")
    print(f"输出文件：{output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())