# Yixuan Skills

个人 Claude Code Skills 集合，用于安全相关的自动化任务。

## 📦 Skills 列表

### daily-cve-report
自动从 NVD 获取过去 24 小时发布的 CVSS >= 7.0 高危漏洞，生成格式化安全报告。

| 项目 | 说明 |
|------|------|
| 目录 | `daily-cve-report/` |
| 依赖 | Python 3.8+, `requests` |
| 输出 | Markdown 格式 CVE 报告 |

**触发词：** `今日 CVE`, `生成 CVE 报告`, `安全漏洞报告`, `每日安全报告`

**快速开始：**
```bash
cd daily-cve-report/scripts
pip install -r requirements.txt
python3 main.py
```

---

### cve-http-filter
从 GitHub CVE 文档筛选远程 HTTP 可触发的漏洞（AV:N + HTTP 可触发）。

**触发词：** `筛选远程HTTP漏洞`, `CVE筛选发企业微信`, `跑一次新的 CVE`

---

### pcap-generator
生成 PCAP 文件用于 Suricata 规则测试。

**触发词：** `生成PCAP`, `create PCAP`, `generate packet capture`

---

## 📁 目录结构

```
yixuan_skills/
├── daily-cve-report/          # CVE 每日报告
│   ├── SKILL.md
│   ├── .env.example
│   └── scripts/
│       ├── fetch_cves.py       # NVD API 抓取 + 分页 + 重试
│       ├── format_report.py    # Markdown 格式化
│       ├── main.py             # 主入口
│       └── requirements.txt
├── cve-http-filter/            # CVE HTTP 筛选
│   └── SKILL.md
├── pcap-generator/             # PCAP 生成
│   └── SKILL.md
├── README.md
├── CLAUDE.md
└── .gitignore
```

## 🔧 配置

### daily-cve-report 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HTTP_PROXY` / `HTTPS_PROXY` | 代理地址（可选） | 无 |
| `NVD_API_URL` | NVD API 地址 | 官方地址 |
| `MIN_CVSS_SCORE` | 最低 CVSS 评分 | 7.0 |
| `CVE_OUTPUT_FILE` | 输出文件名 | cve_report.md |

## ➕ 添加新 Skill

创建目录并添加 `SKILL.md`：

```bash
<skill-name>/
├── SKILL.md        # 必需：name, description, triggers
└── scripts/        # 可选：Python 脚本
```

## 📝 规范

- 每个 Skill 独立目录
- SKILL.md 必须包含 `name` 和 `description`
- 敏感信息不提交（使用 `.env.example` 模板）
- Python 代码使用 `logging` 而非 `print()`
- 配置通过环境变量而非硬编码

## 🚀 使用方法

### 安装 Skills

将仓库克隆到本地后，在 Claude Code 中安装：

```bash
# 克隆仓库
git clone https://github.com/Yxuan18/yixuan_skills.git

# 进入 Claude Code 项目目录
cd your-project/

# 链接 skills 到项目（推荐：项目级安装）
ln -s /path/to/yixuan_skills/daily-cve-report ./skills/

# 或安装到全局
cp -r /path/to/yixuan_skills/* ~/.claude/skills/
```

### 使用 Skills

安装后，通过自然语言触发：

| Skill | 触发方式 |
|-------|----------|
| daily-cve-report | `今日 CVE`、`生成 CVE 报告`、`安全漏洞报告` |
| cve-http-filter | `帮我筛选远程HTTP漏洞`、`跑一次新的 CVE` |
| pcap-generator | `生成PCAP`、`create PCAP`、`test Suricata` |

### 配置（可选）

部分 Skill 支持环境变量配置，参考各目录的 `.env.example`：

```bash
# 在项目根目录创建 .env 文件
cp yixuan_skills/daily-cve-report/.env.example .env
# 编辑 .env 填入代理地址等配置
```