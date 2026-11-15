# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。存档结构变化会提升 `schema_version`。

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
