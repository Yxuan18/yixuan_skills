# Yixuan Skills

个人 Skills 集合，包含在 Claude Code 中注册使用的各种自定义技能。

## 📦 当前 Skills

| Skill | 描述 | 触发词 |
|-------|------|--------|
| [pcap-generator](./pcap-generator/) | 生成 PCAP 文件用于 Suricata 测试 | 生成PCAP, create PCAP, generate packet capture |

## 📁 目录结构

```
yixuan_skills/
├── pcap-generator/          # PCAP 文件生成工具
│   ├── SKILL.md            # Skill 定义文件
│   ├── settings.ini        # 配置文件
│   └── scripts/            # 脚本目录
│       ├── generate_pcap.py
│       └── generate_pcap_direct.py
├── README.md               # 本文件
└── .gitignore              # Git 忽略规则
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