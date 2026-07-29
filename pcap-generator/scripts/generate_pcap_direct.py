#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# generate_pcap_direct.py - 直接使用 scapy 生成 PCAP 文件
# 不依赖 Web API，直接调用 scapy 生成 PCAP
#
# 用法:
#   python scripts/generate_pcap_direct.py request.txt response.txt output.pcap
#   python scripts/generate_pcap_direct.py --template GET /api/test "Hello" output.pcap
#
# 环境变量（可选）:
#   PCAP_SRC_IP   源 IP（默认 192.168.0.1）
#   PCAP_DST_IP   目标 IP（默认 192.168.0.2）
#   PCAP_SRC_MAC  源 MAC（默认 c0:25:a5:80:a4:79）
#   PCAP_DST_MAC  目标 MAC（默认 c0:26:a5:80:a4:79）

import argparse
import os
import random
import re
import sys
import tempfile
from pathlib import Path

from scapy.all import wrpcap
from scapy.layers.inet import IP, TCP


def _get_env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _get_output_dir(output_dir: str | None) -> Path:
    """Return a cross-platform temp directory."""
    if output_dir:
        p = Path(output_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p
    return Path(tempfile.gettempdir())


def generate_pcap(
    request_str: str,
    response_str: str,
    output_name: str,
    output_dir: str | None = None,
    *,
    src_ip: str | None = None,
    dst_ip: str | None = None,
    src_mac: str | None = None,
    dst_mac: str | None = None,
    dst_port: int = 8000,
) -> str:
    """
    直接生成 HTTP PCAP 文件。

    Args:
        request_str:  HTTP 请求原始文本
        response_str: HTTP 响应原始文本
        output_name:  输出文件名（不含扩展名）
        output_dir:   输出目录，默认使用系统临时目录（跨平台）
        src_ip:       源 IP，默认来自 PCAP_SRC_IP 或 192.168.0.1
        dst_ip:       目标 IP，默认来自 PCAP_DST_IP 或 192.168.0.2
        src_mac:      源 MAC，默认来自 PCAP_SRC_MAC
        dst_mac:      目标 MAC，默认来自 PCAP_DST_MAC
        dst_port:     目标端口，默认 8000

    Returns:
        生成的 PCAP 文件路径
    """
    from scapy.layers.inet import Ether  # noqa: F401 — imported late to avoid scapy import error at module level if scapy not installed

    output_path = _get_output_dir(output_dir) / f"{output_name}.pcap"

    # 网络配置 — 支持环境变量覆盖
    src_mac_val = src_mac or _get_env("PCAP_SRC_MAC", "c0:25:a5:80:a4:79")
    dst_mac_val = dst_mac or _get_env("PCAP_DST_MAC", "c0:26:a5:80:a4:79")
    src_ip_val = src_ip or _get_env("PCAP_SRC_IP", "192.168.0.1")
    dst_ip_val = dst_ip or _get_env("PCAP_DST_IP", "192.168.0.2")
    src_port = random.randint(20000, 50000)

    ether_c2s = Ether(src=src_mac_val, dst=dst_mac_val)
    ether_s2c = Ether(src=dst_mac_val, dst=src_mac_val)
    ip_c2s = IP(src=src_ip_val, dst=dst_ip_val)
    ip_s2c = IP(src=dst_ip_val, dst=src_ip_val)

    seq_c = random.randint(1000, 50000)
    seq_s = random.randint(1000, 50000)

    packets = []

    # TCP 三次握手
    syn_packet = ether_c2s / ip_c2s / TCP(sport=src_port, dport=dst_port, seq=seq_c, flags="S")
    seq_c += 1

    syn_ack_packet = ether_s2c / ip_s2c / TCP(sport=dst_port, dport=src_port, flags="SA", seq=seq_s, ack=seq_c)
    seq_s += 1

    ack_packet = ether_c2s / ip_c2s / TCP(sport=src_port, dport=dst_port, seq=seq_c, ack=seq_s, flags="A")

    packets.extend([syn_packet, syn_ack_packet, ack_packet])

    # HTTP 请求
    request_bytes = request_str.encode("utf-8")
    request_packet = (
        ether_c2s / ip_c2s / TCP(sport=src_port, dport=dst_port, seq=seq_c, ack=seq_s, flags="PA") / request_bytes
    )
    packets.append(request_packet)
    seq_c += len(request_bytes)

    # HTTP 响应
    response_bytes = response_str.encode("utf-8")
    response_ack = ether_s2c / ip_s2c / TCP(sport=dst_port, dport=src_port, seq=seq_s, ack=seq_c, flags="A")
    packets.append(response_ack)

    response_packet = (
        ether_s2c / ip_s2c / TCP(sport=dst_port, dport=src_port, seq=seq_s, ack=seq_c, flags="PA") / response_bytes
    )
    packets.append(response_packet)
    seq_s += len(response_bytes)

    # TCP 四次挥手
    fin_packet = ether_c2s / ip_c2s / TCP(sport=src_port, dport=dst_port, seq=seq_c, ack=seq_s, flags="FA")
    packets.append(fin_packet)
    seq_c += 1

    fin_ack = ether_s2c / ip_s2c / TCP(sport=dst_port, dport=src_port, seq=seq_s, ack=seq_c, flags="A")
    packets.append(fin_ack)

    fin_packet2 = ether_s2c / ip_s2c / TCP(sport=dst_port, dport=src_port, seq=seq_s, ack=seq_c, flags="FA")
    packets.append(fin_packet2)
    seq_s += 1

    fin_ack2 = ether_c2s / ip_c2s / TCP(sport=src_port, dport=dst_port, seq=seq_c, ack=seq_s, flags="A")
    packets.append(fin_ack2)

    wrpcap(str(output_path), packets)
    return str(output_path)


def parse_http_content(content: str) -> tuple:
    """
    解析 HTTP 内容，分离 headers 和 body。

    Args:
        content: HTTP 请求或响应文本

    Returns:
        (headers, body) 元组
    """
    header, sep, body = content.partition("\r\n\r\n")
    if body:
        return header, body

    header, sep, body = content.partition("\n\n")
    if body:
        return header.replace("\n", "\r\n"), body.replace("\n", "\r\n")

    return content.replace("\n", "\r\n"), ""


def fix_content_length(request_str: str) -> str:
    """修复 HTTP 请求的 Content-Length"""
    header, body = parse_http_content(request_str)
    cl_match = re.search(r"Content-Length:\s*(\d+)", header, re.IGNORECASE)

    if cl_match:
        expected = int(cl_match.group(1))
        actual = len(body)
        if expected != actual:
            header = re.sub(r"Content-Length:\s*\d+", f"Content-Length: {actual}", header, flags=re.IGNORECASE)
    elif not header.startswith("GET") and not header.startswith("HEAD"):
        header += f"\r\nContent-Length: {len(body)}"

    return header + "\r\n\r\n" + body


def fix_response_length(response_str: str) -> str:
    """修复 HTTP 响应的 Content-Length"""
    header, body = parse_http_content(response_str)
    cl_match = re.search(r"Content-Length:\s*(\d+)", header, re.IGNORECASE)

    if cl_match:
        expected = int(cl_match.group(1))
        actual = len(body)
        if expected != actual:
            header = re.sub(r"Content-Length:\s*\d+", f"Content-Length: {actual}", header, flags=re.IGNORECASE)
    else:
        header += f"\r\nContent-Length: {len(body)}"

    return header + "\r\n\r\n" + body


def generate_from_template(
    request_type: str = "GET",
    path: str = "/",
    response_status: str = "200 OK",
    body: str = "Hello World",
    output_name: str = "output",
    output_dir: str | None = None,
) -> str:
    """
    根据模板生成 PCAP 文件。

    Args:
        request_type:    请求方法 (GET, POST, etc.)
        path:            请求路径
        response_status: 响应状态 (200 OK, 404 Not Found, etc.)
        body:            响应体内容
        output_name:     输出文件名
        output_dir:      输出目录，默认系统临时目录

    Returns:
        生成的 PCAP 文件路径
    """
    request = f"{request_type} {path} HTTP/1.1\r\nHost: example.com\r\n\r\n"
    body_len = len(body)
    response = f"HTTP/1.1 {response_status}\r\nContent-Type: text/html\r\nContent-Length: {body_len}\r\nConnection: close\r\n\r\n{body}"

    return generate_pcap(request, response, output_name, output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="直接生成 PCAP 文件（跨平台）")
    parser.add_argument("request", nargs="?", help="请求内容文件路径，或直接传入请求字符串")
    parser.add_argument("response", nargs="?", help="响应内容文件路径，或直接传入响应字符串")
    parser.add_argument("output", nargs="?", default="output", help="输出文件名（不含扩展名）")
    parser.add_argument("--output-dir", "-o", default=None, help="输出目录（默认系统临时目录）")
    parser.add_argument("--template", action="store_true", help="使用模板模式，忽略 request/response 参数")
    parser.add_argument("--method", default="GET", help="请求方法（模板模式）")
    parser.add_argument("--path", default="/", help="请求路径（模板模式）")
    parser.add_argument("--status", default="200 OK", help="响应状态（模板模式）")
    parser.add_argument("--body", default="Hello World", help="响应体（模板模式）")

    args = parser.parse_args()

    if args.template or not args.request:
        output_path = generate_from_template(
            request_type=args.method,
            path=args.path,
            response_status=args.status,
            body=args.body,
            output_name=args.output,
            output_dir=args.output_dir,
        )
        print(f"PCAP 生成成功: {output_path}")
    else:
        if os.path.isfile(args.request):
            request_str = Path(args.request).read_text(encoding="utf-8")
        else:
            request_str = args.request

        if os.path.isfile(args.response):
            response_str = Path(args.response).read_text(encoding="utf-8")
        else:
            response_str = args.response

        request_str = fix_content_length(request_str)
        response_str = fix_response_length(response_str)

        output_path = generate_pcap(
            request_str,
            response_str,
            args.output,
            args.output_dir,
        )
        print(f"PCAP 生成成功: {output_path}")
