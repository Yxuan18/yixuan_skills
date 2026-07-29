---
name: cnnvd-format
description: |
  将 CNNVD（中国国家信息安全漏洞库）的新格式 XML 转换为旧格式（标签重命名 + 结构归一），可在转换前选择性删除 <PAV> 节点。
  触发词：CNNVD 转换 / CNNVD 旧格式 / 转换 CNNVD XML / cnnvd convert / 新格式转旧格式 / CNNVD PAV 移除
triggers:
  - "CNNVD 转换"
  - "CNNVD 旧格式"
  - "转换 CNNVD XML"
  - "cnnvd convert"
  - "新格式转旧格式"
  - "CNNVD PAV 移除"
  - "去除 CNNVD PAV"
---

# CNNVD Format

将 CNNVD 新格式 XML 转换为旧格式（标签重命名 + 结构归一），并在转换前选择性删除 `<PAV>...</PAV>` 节点。

## 快速启动

```bash
# 推荐：完整管道（删除 PAV + 格式转换）
cd cnnvd_format/scripts
python3 process_cnnvd.py -f input.xml -o output.xml

# 仅删除 <PAV> 节点
python3 remote_pav.py -f input.xml -o no_pav.xml

# 仅做格式转换
python3 transform_cnnvd_xml.py -f input.xml -o output.xml
```

## 转换规则

新格式 → 旧格式的标签映射：

| 新格式标签 | 旧格式标签 |
|-----------|-----------|
| `cnnvd_items` | `entry` |
| `cnnvd_id` | `vuln-id` |
| `severity/technicalseverity` + `severity/overallseverity` | `severity`（优先 `overallseverity`） |
| `vuln_type` | `vuln-type` |
| `vuln_descript` | `vuln-descript` |
| `cve_id` | `other-id/cve-id`（同时插入空 `bugtraq-id`） |

根节点：

```xml
<!-- 新格式 -->
<cnnvd publisher="..." date="..." date_range="..." format="...">
<!-- 旧格式 -->
<cnnvd cnnvd_xml_version="1.0" pub_date="...">
```

旧格式中只保留这两个属性。

## 输出文件名

未指定 `-o` 时：

- `process_cnnvd.py` → `<输入文件名>_old_format.xml`
- `remote_pav.py` → `<输入文件名>_no_pav.xml`
- `transform_cnnvd_xml.py` → `<输入文件名>_old_format.xml`

## 配置

详见 [`CONFIG.md`](CONFIG.md)（环境要求、可移植性说明、参数细节）。

## 常见问题

详见 [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)（XML 解析失败、`<PAV>` 未闭合、编码问题等）。
