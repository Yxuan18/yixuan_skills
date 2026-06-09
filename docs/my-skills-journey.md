# 从「用别人的技能」到「写自己的 Skill」—— 我的 CVE 自动化之路
### How I Built a CVE Automation Skill with Claude Code

## 缘起：一次顺手的功能，点燃了自动化的念头

事情要从一次日常安全运营说起。如果你也是安全团队的一员，你可能懂这种痛——

每天早上，安全团队都需要从 NVD（National Vulnerability Database）拉取过去 24 小时新发布的高危漏洞，整理成报告发给同事。过去这套流程是纯手工的：打开 NVD 网页、设置日期筛选、复制 CVSS ≥ 7.0 的漏洞、逐条整理……一次要花 20-30 分钟。

某天，我在逛 GitHub 时偶然发现了别人写的 CVE 筛选工具。它从 GitHub 托管的 CVE 文档中提取编号，调用 NVD API 获取 CVSS 向量，自动过滤出远程网络可触发（AV:N）的漏洞，最后生成报告推送到企业微信。

我试了一下——好使。

然后脑子里冒出来的第一个念头是：**既然别人的方法可以用，那我自己也能用。**

## 核心洞察：自然语言才是终极接口

进一步想，这套流程有几个明确的步骤：

1. 从 NVD API 拉取过去 24 小时的漏洞
2. 筛选 CVSS ≥ 7.0 的高危项
3. 解析 CVE 描述中的 CWE（通用弱点枚举）分类，生成 IOC（威胁指标，如相关域名、IP、哈希值）
4. 关联修复建议和补丁链接
5. 按预设模板生成 Markdown 格式报告

这些步骤完全可以用自然语言描述，然后交给 AI 去执行。问题在于：如果每次都要把这些步骤重新说一遍，就太浪费了。

**更好的方式是：把流程固化成一个 Skill（技能），用自然语言触发它。**

## 转化过程：从脚本到 Skill 的三步走

### 第一步：理解现有实现

我先完整跑通了别人的脚本，搞清楚每个环节的数据流向：

```
NVD API → Python requests → CVSS 筛选 → IOC 生成 → Markdown 格式化
```

这里有一个坑：直连 NVD API 在某些网络环境下会被重置，需要走代理。借鉴了同一仓库下 `cve-http-filter` 的代理处理方式（这个目录原本就有，是另一个用途的 CVE 筛选工具），从环境变量 `HTTP_PROXY` / `HTTPS_PROXY` 读取代理配置，默认走 `127.0.0.1:7897`。

### 第二步：模块化拆分

把脚本拆成三个独立模块，按职责分离，便于独立测试和复用。具体拆分为：

| 文件 | 职责 |
|------|------|
| `fetch_cves.py` | 从 NVD API 获取数据，带代理支持 |
| `format_report.py` | 将 CVE 数据格式化为 Markdown |
| `main.py` | 主入口，串联整个流程 |

这样每个模块都可以独立测试、独立复用。

### 第三步：写 SKILL.md，定义触发词

Skill 的核心是 `SKILL.md`，其中最关键的是 frontmatter 的 `description` 字段——这是 Claude Code 判断是否触发该 Skill 的依据。以下是一个完整的 frontmatter 示例：

```yaml
---
name: daily-cve-report
description: |
  Daily CVE report generation — automatically fetch CVSS >= 7.0 high-severity 
  vulnerabilities published in the last 24 hours from NVD, generate formatted 
  security reports (including CVE details, IOC indicators, remediation 
  suggestions), and optionally create GitHub Issues.
  USE THIS SKILL whenever users say "today's CVE", "generate CVE report", 
  "daily CVE", "security vulnerability report", "run CVE", "CVE daily report",
  "今日 CVE", "生成 CVE 报告", "安全漏洞报告", "跑一下 CVE", "CVE 日报", 
  "每日安全报告".
---
```

触发词覆盖了中英文、日常口语和专业术语，确保在不同场景下都能命中。

## 成果：用 Claude Code 写 Skill，一句话触发，实测约 3 秒出报告

用 Claude Code 写 Skill 的核心优势是：**你只需要描述工作流，剩下的交给 AI。** 当你说出触发词，Claude Code 加载 Skill 中的指令描述，引导 AI 逐步调用 NVD API 获取数据、格式化输出，全程无需手动操作。

现在，运行一次 CVE 日报只需要说一句：

> "今日 CVE"

实测约 3 秒即可生成 `cve_report.md`，整个过程无需复制粘贴任何代码，无需记住任何命令参数。

## 更大的图景：把重复变成复用

回过头来看，这条路的本质是：

**把「别人做过的、有效的自动化流程」，通过自然语言接口固化成自己的工具。** 用 Claude Code 写 Skill，就是把这一套思路落地的最佳方式：写一次，触发 N 次。

不是重复造轮子，而是把它装进自己的工具箱。这个思维模式可以复制到任何重复性高的安全运营场景：

- 每天查一次资产暴露面 → 写成 Skill，一句话触发
- 每次上线前跑一组检测规则 → 写成 Skill，输入目标地址自动跑
- 每周汇总一次威胁情报 → 写成 Skill，自动生成摘要

Skill 的价值在于：写一次，触发 N 次。每次触发都是零认知负荷的。

## 写在最后

我最大的感受是：**工具的价值不在于它有多复杂，而在于它能不能被一句话唤醒。**

当你发现一个重复了三天的手动操作，停下来把它变成 Skill。第四天开始，你就已经在用「AI + 自然语言」驱动安全运营了。

> 如果你也在做安全运营，不妨试试：找一个你每天都在重复的手工任务，尝试把它描述成一个 Skill。你可能会发现，门槛比你想象的低得多。

**配套资源：** [daily-cve-report 源码](https://github.com/Yxuan18/yixuan_skills/tree/main/daily-cve-report) | [完整 Skill 集合](https://github.com/Yxuan18/yixuan_skills)

---

*相关 Skill 已开源：[yixuan_skills](https://github.com/Yxuan18/yixuan_skills)*