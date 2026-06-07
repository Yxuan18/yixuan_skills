#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# generate_pcap_direct.py - 直接使用 scapy 生成 PCAP 文件
# 不依赖 Web API，直接调用 web app 的函数生成 PCAP

import sys
import os
import re
import random

# 添加 web_apps 目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scapy.all import *
from scapy.layers.inet import IP, TCP, Ether


def generate_pcap(request_str: str, response_str: str, output_name: str, output_dir: str = None) -> str:
    """
    直接生成 HTTP PCAP 文件

    Args:
        request_str: HTTP 请求原始文本
        response_str: HTTP 响应原始文本
        output_name: 输出文件名（不含扩展名）
        output_dir: 输出目录，默认为 /tmp

    Returns:
        生成的 PCAP 文件路径
    """
    if output_dir is None:
        output_dir = "/tmp"

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 网络配置
    src_mac = "c0:25:a5:80:a4:79"
    dst_mac = "c0:26:a5:80:a4:79"
    src_ip = "192.168.0.1"
    dst_ip = "192.168.0.2"
    dst_port = 8000
    src_port = random.randint(20000, 50000)

    # 准备以太网 / IP 层
    ether_c2s = Ether(src=src_mac, dst=dst_mac)
    ether_s2c = Ether(src=dst_mac, dst=src_mac)
    ip_c2s = IP(src=src_ip, dst=dst_ip)
    ip_s2c = IP(src=dst_ip, dst=src_ip)

    # 初始化序列号
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
    request_bytes = request_str.encode('utf-8')
    request_packet = ether_c2s / ip_c2s / TCP(sport=src_port, dport=dst_port, seq=seq_c, ack=seq_s, flags="PA") / request_bytes
    packets.append(request_packet)

    seq_c += len(request_bytes)

    # HTTP 响应
    response_bytes = response_str.encode('utf-8')
    response_ack = ether_s2c / ip_s2c / TCP(sport=dst_port, dport=src_port, seq=seq_s, ack=seq_c, flags="A")
    packets.append(response_ack)

    response_packet = ether_s2c / ip_s2c / TCP(sport=dst_port, dport=src_port, seq=seq_s, ack=seq_c, flags="PA") / response_bytes
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

    # 生成 PCAP 文件
    output_path = os.path.join(output_dir, f"{output_name}.pcap")
    wrpcap(output_path, packets)

    return output_path


def parse_http_content(content: str) -> tuple:
    """
    解析 HTTP 内容，分离 headers 和 body

    Args:
        content: HTTP 请求或响应文本

    Returns:
        (headers, body) 元组
    """
    # 尝试用 \r\n\r\n 分割
    header, sep, body = content.partition('\r\n\r\n')
    if body:
        return header, body

    # 如果没有 \r\n\r\n，尝试用 \n\n 分割
    header, sep, body = content.partition('\n\n')
    if body:
        return header.replace('\n', '\r\n'), body.replace('\n', '\r\n')

    # 如果都没有，把整个内容当作 headers
    return content.replace('\n', '\r\n'), ''


def fix_content_length(request_str: str) -> str:
    """
    修复 HTTP 请求的 Content-Length
    """
    header, body = parse_http_content(request_str)

    # 检查是否已有 Content-Length
    cl_match = re.search(r'Content-Length:\s*(\d+)', header, re.IGNORECASE)

    if cl_match:
        # 更新已有 Content-Length
        expected = int(cl_match.group(1))
        actual = len(body)
        if expected != actual:
            header = re.sub(r'Content-Length:\s*\d+', f'Content-Length: {actual}', header, flags=re.IGNORECASE)
    else:
        # 添加 Content-Length
        if not header.startswith('GET'):
            header += f'\r\nContent-Length: {len(body)}'

    return header + '\r\n\r\n' + body


def fix_response_length(response_str: str) -> str:
    """
    修复 HTTP 响应的 Content-Length
    """
    header, body = parse_http_content(response_str)

    # 检查是否已有 Content-Length
    cl_match = re.search(r'Content-Length:\s*(\d+)', header, re.IGNORECASE)

    if cl_match:
        expected = int(cl_match.group(1))
        actual = len(body)
        if expected != actual:
            header = re.sub(r'Content-Length:\s*\d+', f'Content-Length: {actual}', header, flags=re.IGNORECASE)
    else:
        header += f'\r\nContent-Length: {len(body)}'

    return header + '\r\n\r\n' + body


def generate_from_template(request_type: str = "GET", path: str = "/",
                          response_status: str = "200 OK",
                          body: str = "Hello World",
                          output_name: str = "output") -> str:
    """
    根据模板生成 PCAP 文件

    Args:
        request_type: 请求方法 (GET, POST, etc.)
        path: 请求路径
        response_status: 响应状态 (200 OK, 404 Not Found, etc.)
        body: 响应体内容
        output_name: 输出文件名

    Returns:
        生成的 PCAP 文件路径
    """
    # 构建请求
    request = f"{request_type} {path} HTTP/1.1\r\nHost: example.com\r\n\r\n"

    # 构建响应
    body_len = len(body)
    response = f"HTTP/1.1 {response_status}\r\nContent-Type: text/html\r\nContent-Length: {body_len}\r\nConnection: close\r\n\r\n{body}"

    return generate_pcap(request, response, output_name)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='直接生成 PCAP 文件')
    parser.add_argument('request', nargs='?', help='请求内容文件路径，或直接传入请求字符串')
    parser.add_argument('response', nargs='?', help='响应内容文件路径，或直接传入响应字符串')
    parser.add_argument('output', nargs='?', default='output', help='输出文件名')
    parser.add_argument('--output-dir', '-o', default='/tmp', help='输出目录')

    args = parser.parse_args()

    if args.request and args.response:
        # 从文件或字符串读取
        if os.path.isfile(args.request):
            with open(args.request, 'r') as f:
                request_str = f.read()
        else:
            request_str = args.request

        if os.path.isfile(args.response):
            with open(args.response, 'r') as f:
                response_str = f.read()
        else:
            response_str = args.response

        # 修复 Content-Length
        request_str = fix_content_length(request_str)
        response_str = fix_response_length(response_str)

        # 生成 PCAP
        output_path = generate_pcap(request_str, response_str, args.output, args.output_dir)
        print(f"PCAP 生成成功: {output_path}")
    else:
        # 示例：生成简单的 GET/200 PCAP
        print("示例：生成简单的 GET 请求 PCAP")
        output_path = generate_from_template(
            request_type="GET",
            path="/api/test",
            response_status="200 OK",
            body="<html><body>Test OK</body></html>",
            output_name="get_test"
        )
        print(f"PCAP 生成成功: {output_path}")