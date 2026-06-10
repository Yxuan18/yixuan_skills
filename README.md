# Yixuan Skills

个人 Claude Code Skills 集合，用于安全相关的自动化任务。

## Skills 列表

### daily-cve-report
自动从 NVD 获取过去 24 小时发布的 CVSS >= 7.0 高危漏洞，生成格式化安全报告。

| 触发词 | 说明 |
|--------|------|
| `今日 CVE`、`CVE 日报` | 获取今日 CVE 报告 |
| `生成 CVE 报告`、`每日安全报告` | 生成完整报告 |

**文档：**
- `SKILL.md` — 触发词 + 快速启动
- `CONFIG.md` — 环境变量 + 代理配置
- `IOC.md` — CWE → IOC 映射表
- `TROUBLESHOOTING.md` — 常见问题处理

### cve-http-filter
从 GitHub CVE 文档筛选远程 HTTP 可触发的漏洞（AV:N）。

| 触发词 | 说明 |
|--------|------|
| `筛选远程HTTP漏洞` | 仅筛选 |
| `CVE筛选发企业微信` | 筛选 + 推送 |

**文档：**
- `SKILL.md` — 触发词 + 快速启动
- `CONFIG.md` — 环境变量 + 代理配置
- `TROUBLESHOOTING.md` — 常见问题处理

### pcap-generator
生成 PCAP 文件用于 Suricata 规则测试。

| 触发词 | 说明 |
|--------|------|
| `生成PCAP`、`create PCAP` | 生成数据包捕获 |
| `test Suricata`、`simulate HTTP traffic` | 模拟 HTTP 流量 |

**文档：**
- `SKILL.md` — 触发词 + 快速启动
- `PATTERNS.md` — 常见 HTTP 模式 curl 命令
- `API.md` — `generate_pcap_direct.py` 函数接口
- `TROUBLESHOOTING.md` — 常见问题处理

## 目录结构

```
yixuan_skills/
├── daily-cve-report/
│   ├── SKILL.md              # 触发词 + 快速启动
│   ├── CONFIG.md             # 环境变量
│   ├── IOC.md                # CWE → IOC
│   ├── TROUBLESHOOTING.md    # 常见问题
│   └── scripts/
│       ├── main.py
│       ├── fetch_cves.py
│       ├── format_report.py
│       └── requirements.txt
├── cve-http-filter/
│   ├── SKILL.md
│   ├── CONFIG.md
│   ├── TROUBLESHOOTING.md
│   └── cve_http_filter.py
├── pcap-generator/
│   ├── SKILL.md
│   ├── PATTERNS.md           # curl 模式
│   ├── API.md                # 函数接口
│   ├── TROUBLESHOOTING.md
│   ├── settings.ini
│   └── scripts/
│       ├── generate_pcap.py           # Web API 封装
│       └── generate_pcap_direct.py  # scapy 直接生成
├── README.md
├── CLAUDE.md
└── .gitignore
```

## 安装

```bash
# 克隆仓库
git clone https://github.com/Yxuan18/yixuan_skills.git

# 项目级安装（推荐）
ln -s /path/to/yixuan_skills/daily-cve-report ./skills/

# 全局安装
cp -r /path/to/yixuan_skills/* ~/.claude/skills/
```

## 开发规范

- SKILL.md 必须包含 `name` 和 `description`
- 敏感信息不提交（使用 `.env.example` 模板）
- Python 代码使用 `logging` 而非 `print()`
- 配置通过环境变量而非硬编码
- 文档按需拆分，SKILL.md 只保留必要信息