---
description: cnnvd_format 环境要求、命令行参数、可移植性约束和导入路径配置
---

# 配置

## 环境要求

- **Python**：3.10+（脚本使用 `from __future__ import annotations`、`ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))`、`pathlib.Path` 等现代特性）
- **依赖**：仅使用标准库（`xml.etree.ElementTree`, `argparse`, `pathlib`, `logging`），无需 `pip install`
- **平台**：跨平台（macOS / Linux / Windows）

## 可移植性

整个 skill 设计为可任意复制到本地任意路径后立即运行：

- 所有脚本只依赖 Python 标准库
- 没有硬编码路径、代理、用户名或绝对路径
- 三个脚本之间的相互 import 假定它们位于同一目录（见下文），SKILL.md 中所有示例都使用相对路径 `cd cnnvd_format/scripts`
- 输入/输出路径通过 CLI 参数显式传入，不依赖 cwd

### 关键运行约束

`process_cnnvd.py` 用相对路径 import：

```python
from remote_pav import remove_pav
from transform_cnnvd_xml import transform_xml, default_output_path
```

因此必须满足以下任一条件之一：

1. **从 `scripts/` 目录运行**（推荐，与 SKILL.md 的所有示例一致）：
   ```bash
   cd cnnvd_format/scripts
   python3 process_cnnvd.py -f input.xml -o output.xml
   ```

2. **把 `scripts/` 加到 `PYTHONPATH`**：
   ```bash
   PYTHONPATH=cnnvd_format/scripts python3 cnnvd_format/scripts/process_cnnvd.py -f input.xml
   ```

不要把单个脚本单独复制到其他目录——这样 import 会断。

## 命令行参数

### `process_cnnvd.py`（完整管道）

| 参数 | 说明 | 默认 |
|------|------|------|
| `-f` / `--file` | 输入 XML 文件路径（必填） | — |
| `-o` / `--output` | 输出文件路径 | `<输入文件名>_old_format.xml` |
| `--xml-version` | 旧格式根节点的 `cnnvd_xml_version` | `1.0` |

### `remote_pav.py`（仅删除 PAV）

| 参数 | 说明 | 默认 |
|------|------|------|
| `-f` / `--file` | 输入 XML 文件路径（必填） | — |
| `-o` / `--output` | 输出文件路径 | `<输入文件名>_no_pav.xml` |

内部参数 `chunk_size`（默认 1 MB）和 `max_buffer_size`（默认 10 MB）目前不可通过命令行调整，需要时直接修改脚本。

### `transform_cnnvd_xml.py`（仅格式转换）

| 参数 | 说明 | 默认 |
|------|------|------|
| `-f` / `--file` | 输入新格式 XML（必填） | — |
| `-o` / `--output` | 输出文件路径 | `<输入文件名>_old_format.xml` |
| `--xml-version` | 旧格式根节点的 `cnnvd_xml_version` | `1.0` |

## 文件结构

```
cnnvd_format/
├── SKILL.md                  # 触发词 + 快速启动（本文档）
├── CONFIG.md                 # 环境要求 + 参数细节 + 可移植性
├── TROUBLESHOOTING.md        # 常见问题处理
└── scripts/
    ├── process_cnnvd.py      # 主入口：完整管道
    ├── remote_pav.py         # 流式删除 <PAV> 节点
    └── transform_cnnvd_xml.py # 新格式转旧格式
```

## 处理流程

`process_cnnvd.py` 内部按以下顺序执行：

1. **删除 `<PAV>`**（调用 `remote_pav.py`）→ 输出临时中间文件 `<输入文件名>_no_pav.xml`
2. **格式转换**（调用 `transform_cnnvd_xml.py`）→ 输出最终旧格式文件
3. **清理临时文件**

如果任一步骤失败,临时文件会被自动删除,不会留下垃圾。
