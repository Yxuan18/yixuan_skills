#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def remove_pav(input_file: str, output_file: str, chunk_size: int = 1024 * 1024) -> bool:
    """
    流式删除 XML 中所有 <PAV>...</PAV> 节点

    参数:
        input_file: 原始 XML 文件路径
        output_file: 输出文件路径
        chunk_size: 每次读取大小，默认 1MB

    返回:
        True 表示成功，False 表示失败
    """
    start_tag = b"<PAV>"
    end_tag = b"</PAV>"
    max_buffer_size = 10 * 1024 * 1024  # 10MB 上限，防止内存爆炸

    removing = False
    buffer = b""

    try:
        with open(input_file, "rb") as fin, \
             open(output_file, "wb") as fout:

            while True:
                chunk = fin.read(chunk_size)

                if not chunk:
                    break

                buffer += chunk

                # P1: 防止 buffer 无限增长
                if len(buffer) > max_buffer_size:
                    logger.warning(f"Buffer 超过 {max_buffer_size / 1024 / 1024}MB，可能存在未闭合标签")
                    return False

                while True:
                    if removing:
                        end_index = buffer.find(end_tag)

                        if end_index == -1:
                            # 还没找到结束标签，保留最后几个字节防止标签跨chunk
                            buffer = buffer[-len(end_tag):]
                            break

                        # 删除到 </PAV>
                        buffer = buffer[end_index + len(end_tag):]
                        removing = False

                    else:
                        start_index = buffer.find(start_tag)

                        if start_index == -1:
                            # 没找到开始标签，写入安全部分
                            keep = len(buffer) - len(start_tag)

                            if keep > 0:
                                fout.write(buffer[:keep])
                                buffer = buffer[keep:]

                            break

                        else:
                            # 写入PAV之前内容
                            fout.write(buffer[:start_index])
                            buffer = buffer[start_index + len(start_tag):]
                            removing = True

            # 写入剩余内容
            if buffer and not removing:
                fout.write(buffer)

        return True

    except FileNotFoundError:
        logger.error(f"文件不存在: {input_file}")
        return False
    except PermissionError:
        logger.error(f"无权限访问文件: {input_file}")
        return False
    except OSError as e:
        logger.error(f"文件操作失败: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="流式删除 XML 中所有 <PAV>...</PAV> 节点"
    )
    parser.add_argument(
        "-f", "--file",
        required=True,
        help="输入 XML 文件路径"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出文件路径（默认: <输入文件名>_no_pav.xml）"
    )
    args = parser.parse_args()

    src = args.file
    dst = args.output

    # 自动生成输出文件名
    if not dst:
        base, ext = os.path.splitext(src)
        dst = f"{base}_no_pav{ext}"

    logger.info(f"输入: {src}")
    logger.info(f"输出: {dst}")

    success = remove_pav(src, dst)

    if success:
        output_size = os.path.getsize(dst) / 1024 / 1024
        logger.info(f"完成，输出文件大小: {output_size:.2f} MB")
    else:
        logger.error("处理失败，请检查输入文件")
