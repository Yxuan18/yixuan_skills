# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库概述

这是一个 Claude Code Skills 集合仓库，用于安全相关的自动化任务。每个 skill 是独立的模块，专注于特定场景。

## 项目结构

```
yixuan_skills/
├── cve-http-filter/    # CVE 远程 HTTP 漏洞筛选 skill
├── pcap-generator/      # PCAP 文件生成 skill（用于复现漏洞流量）
├── README.md
└── CLAUDE.md
```

## Skills

### cve-http-filter
从 GitHub 托管的 CVE 文档（如 `https://github.com/ycdxsb/PocOrExp_in_Github/blob/main/Today.md`）提取 CVE 编号，过滤出满足以下条件的漏洞：
- **AV:N**（CVSS 向量中 Attack Vector = Network，即远程网络可触发）
- **HTTP 可触发**（漏洞可通过发送 HTTP 请求来触发，而非本地/Bluetooth/物理接触/非HTTP协议）

使用方法（优先 Python 脚本，回退浏览器）：
1. Python 直接请求 GitHub Raw URL 提取 CVE
2. NVD REST API (`https://services.nvd.nist.gov/rest/json/cves/2.0`) 获取 CVSS 向量
3. 按 AV:N 筛选，输出 Markdown 表格
4. curl subprocess + 代理推送企业微信

触发场景：
- "帮我筛选远程HTTP漏洞"
- "CVE筛选发企业微信"
- "跑一次新的 CVE"
- "过一遍，发我企业微信"

### pcap-generator
生成 PCAP 文件用于 Suricata 规则测试。

## 开发规范

- 每个 Skill 独立一个目录
- SKILL.md 中必须包含 `name` 和 `description`
- 敏感信息（如 API keys）不要提交到仓库

## Git 工作流

```bash
# 添加更改
git add .

# 提交
git commit -m "feat: add <feature-name>"

# 推送到 GitHub
git push
```