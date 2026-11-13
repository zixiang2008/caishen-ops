# caishen-ops

财绅的家庭实验室云侧运维仓库，全部由 GitHub Actions 免费托管（电脑关机也照跑）。

## Workflows

### 1. Uptime Monitor（每 30 分钟）

检查 5 个公网端点：MausBot、caishen.today、NowledgeMem、Hermes(小曼)、Agent2api。

- 全部正常 → 无动作；有故障 → 自动开/更新 `uptime` 标签的 issue，恢复后自动关闭
- 支持手动触发（workflow_dispatch）
- 结果写入 run summary

### 2. YouTube Radar（每天曼谷 08:00）

抓取 **944 个订阅频道**的 RSS，汇总最近 24 小时的新视频：

- `radar.md` — 人类可读报告（按频道分组）
- `data/radar-latest.json` — 机器可读，MausBot 晨报直接引用：
  `https://raw.githubusercontent.com/zixiang2008/caishen-ops/main/data/radar-latest.json`
- `data/radar-state.json` — 已见视频状态（防止重复上报）

## 本仓库与机器人团队的关系

- **Nimbus 云与AI管家**：负责本仓库健康、检查 uptime issue、按需重跑 workflow（用 `git credential fill` 取 token 调 GitHub API）
- **MausBot 晨报**：引用 radar-latest.json 做"订阅新内容"板块
- **Lex 律政助手**：如需监控 nidec.com 等页面，可在 uptime_check.py 加端点
