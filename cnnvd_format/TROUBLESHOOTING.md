---
description: cnnvd_format 常见问题处理，含 XML 解析失败、PAV 未闭合、Import Error 解决
---

# 常见问题

## XML 解析失败

```
错误：XML 解析失败：not well-formed (invalid token): line N, column M
```

常见原因：

- 标签未闭合（最常见的来源就是未成对的 `<PAV>`，建议先用 `remote_pav.py` 单独跑一遍）
- 特殊字符未转义（`<` / `&` 出现在文本里）
- 编码不是 UTF-8（脚本以 UTF-8 读取，编码不匹配会触发 `ParseError`）

排查：

```bash
# 先单独验证 XML 合法性
python3 -c "import xml.etree.ElementTree as ET; ET.parse('input.xml')"
```

## 转换后条目数量为 0

`process_cnnvd.py` 报告 `已转换 0 个 cnnvd_items 节点`：

- 确认输入是新格式（标签是 `cnnvd_items` 而不是 `entry`）。已经是旧格式的 XML 不会出错，但也不会有转换动作
- 检查根节点确认是否为 `<cnnvd>`

## `<PAV>` 未闭合

`remote_pav.py` 在 buffer 超过 10 MB 时报错：

```
Buffer 超过 10.0MB，说明存在未闭合标签
```

这意味着存在 `<PAV>` 开始标签但没有对应的 `</PAV>`。常见原因：

- 输入文件被人为截断
- PAV 节点内部嵌套了同名标签（脚本不做嵌套识别,只看字符串匹配）
- 编码被破坏，导致 `<PAV>` 字节序列跨字符边界

处理：人工检查源 XML，或调大 `remote_pav.py` 内的 `max_buffer_size`（仅用于调试）。

## 中文环境输出乱码

设置 Python 输出编码：

```bash
PYTHONIOENCODING=utf-8 python3 process_cnnvd.py -f input.xml
```

XML 文件本身始终以 UTF-8 编码读取和写出，与终端无关。

## Import Error

```
ModuleNotFoundError: No module named 'remote_pav'
```

`process_cnnvd.py` 用相对路径 import 另外两个脚本。两种解决方式：

```bash
# 方式 1：从 scripts/ 目录运行
cd cnnvd_format/scripts
python3 process_cnnvd.py -f input.xml

# 方式 2：把 scripts/ 加到 PYTHONPATH
PYTHONPATH=cnnvd_format/scripts python3 cnnvd_format/scripts/process_cnnvd.py -f input.xml
```

不要只复制单个脚本到其他目录。

## 输出路径

未指定 `-o` 时,默认输出文件名：

| 输入 | 默认输出 |
|------|---------|
| `input.xml`（走 `process_cnnvd.py` 或 `transform_cnnvd_xml.py`） | `input_old_format.xml` |
| `input.xml`（只走 `remote_pav.py`） | `input_no_pav.xml` |

输出文件路径不能与输入文件相同（脚本会拒绝并报错 `输出文件不能与输入文件相同`）。

## 流式处理 vs 内存加载

`remote_pav.py` 是流式处理（1 MB 块），适合处理 GB 级别的超大 CNNVD 文件。

`transform_cnnvd_xml.py` 用 `ET.parse` 整体加载到内存。处理超大文件时如果内存不足，需要把脚本改成流式或 SAX 解析。当前实现没有可调参数。
