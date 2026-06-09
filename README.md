# Yixuan Skills

个人 Skills 集合，包含在 Claude Code 中注册使用的各种自定义技能。

## 📦 当前 Skills

| Skill | 描述 | 触发词 |
|-------|------|--------|
| [daily-cve-report](./daily-cve-report/) | 自动从 NVD 获取 CVSS ≥ 7.0 高危漏洞，生成安全报告并推送企业微信 | 今日CVE, 生成CVE报告, 安全漏洞报告, 每日安全报告 |
| [cve-http-filter](./cve-http-filter/) | 从 GitHub CVE 文档筛选远程 HTTP 可触发漏洞 | 筛选远程HTTP漏洞, CVE筛选发企业微信, 跑一次新的CVE |
| [pcap-generator](./pcap-generator/) | 生成 PCAP 文件用于 Suricata 测试 | 生成PCAP, create PCAP, generate packet capture |

## 📁 目录结构

```
yixuan_skills/
├── daily-cve-report/       # CVE 每日安全报告工具
│   └── SKILL.md
├── cve-http-filter/        # CVE 远程 HTTP 漏洞筛选工具
│   └── SKILL.md
├── pcap-generator/        # PCAP 文件生成工具
│   ├── SKILL.md
│   ├── settings.ini
│   └── scripts/
│       ├── generate_pcap.py
│       └── generate_pcap_direct.py
├── README.md
├── CLAUDE.md
└── .gitignore
```

## 🚀 使用方法

Skills 通过 Claude Code 的 `/skills` 命令管理。

### 查看已安装的 Skills

```bash
/skills
```

### 在新环境中恢复 Skills

将仓库克隆到本地后，参考各个 Skill 的 SKILL.md 进行配置和注册。

## ➕ 添加新 Skill

添加新的 Skill 时，建议遵循以下目录结构：

```
<skill-name>/
├── SKILL.md        # Skill 定义（必需）：名称、描述、触发词、工作流
├── settings.ini    # 配置文件（如需要）
└── scripts/        # 脚本目录（如需要）
```

### SKILL.md 模板

```markdown
---
name: <skill-name>
description: <一句话描述 Skill 的功能>
---

# <Skill 名称>

详细描述...

## 触发词
- <触发词1>
- <触发词2>

## 工作流
1. <步骤1>
2. <步骤2>

## 配置（如需要）
...
```

## 📝 规范

- 每个 Skill 独立一个目录
- SKILL.md 中必须包含 `name` 和 `description`
- 配置文件使用 `.ini` 格式
- 敏感信息（如 API keys）不要提交到仓库