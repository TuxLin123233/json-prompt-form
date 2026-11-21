# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。存档结构变化会提升 `schema_version`。

## v2.3.0 — 2026-11-21

### 新增
- 36 个场景各配一个 Lucide 线性图标，卡片一眼可区分；图标通过 CSS mask 跟随卡片颜色，保持灰白极简。
- `assets/icons/` 收录 36 个 SVG 与 Lucide 的 ISC 许可；README、页脚增加 Lucide 致谢。
- `scenarios.json` 每项增加 `icon` 字段，`validate.py` 校验对应图标文件存在。

## v2.2.1 — 2026-11-21

### 新增
- `scenarios.json`：36 个场景的机器可读索引（名称、描述、分类、时长、难度、受众、关键词）。
- `scripts/validate.py` 增加场景索引一致性校验：`scenarios.json` ↔ `examples/` ↔ `index.html` ↔ `README.md`。
- 首页搜索接入 `scenarios.json` 的关键词，支持同义词（如「失眠」命中睡眠、「社恐」命中社交焦虑）。
- `scripts/generate_examples.py` 的场景元信息改为读取 `scenarios.json`。

### 修复
- 自定义生成器功能选项高度不一致（`label` 样式误伤 `.check`）。

## v2.2.0 — 2026-11-21

### 新增
- 9 个新场景（中文共 36 个）：跑步、久坐体态、社交焦虑、自我关怀、学车考驾照、论文毕设、职场沟通、副业启动、专注力。
- 首页场景列表、README、demo、llms.txt、manifest 与发布清单同步到 36 个。

## v2.1.0 — 2026-11-21

### 新增
- 第 27 个场景「项目推进」：`examples/project.json`（含英文与已填示例）。
- `updates.json`：版本迁移清单，记录每个版本的字段增删、改名与默认值。
- 模板内嵌 `compatibility.updates`：续接旧存档时 AI 自动迁移，并用一行说明升级结果。
- `scripts/migrate.py` 改为读取 `updates.json`，与 AI 共用同一份迁移规则。
- `scripts/validate.py` 校验迁移清单、模板漂移和示例版本一致性。

### 变更
- `schema_version` 提升到 2.1.0。
- README、FAQ、llms.txt 增加旧存档续接说明。
- 首页、生成器、检查器改为极简灰白插画风；插画来自 unDraw 并统一改为灰白配色，页脚补致谢与版权（LinSifan）。

## v2.0.0 — 2026-11-15

### 新增
- `archive_modes`：完整存档 / 精简存档两种模式，大幅缩短存档体积。
- 26 个场景的「已填示例存档」：`examples/filled/`。
- 自定义生成器 `builder.html` 和存档检查器 `checker.html`。
- PWA 支持：可添加到手机主屏幕、离线打开。
- `scripts/migrate.py`：把旧存档迁移到当前结构。
- `llms.txt`、英文场景模板 `examples/en/`。
- 场景搜索和「最近使用」。

### 变更
- 首页增加搜索、最近使用、生成器 / 检查器入口。
- README 增加新功能说明与流程图。

## v1.2.0 — 2026-11-14

### 新增
- 场景模板从 14 个增加到 26 个。
- GitHub Pages 一键复制页。
- 英文 README、FAQ、示例对话、贡献指南。

## v1.1.0 — 2026-11-14

### 新增
- 存档 JSON Schema、生成脚本、校验脚本。
- 6 个基础场景模板。
- 功能过期提醒、演化建议、拒绝记录、分段存档。

## v1.0.0 — 2026-11-14

### 新增
- 第一版 `form.json`：长期陪伴提示词规范。
- README 与使用说明。
