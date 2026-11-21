# 贡献指南

感谢你愿意补充场景或改进模板。

## 新增一个场景

1. 在 `scripts/generate_examples.py` 的 `SCENARIOS` 里加一项，包含：
   - `goal`
   - `identity`（`what / why / how`）
   - `scene`（`what / why / how`）
   - `functions`（5–8 个，用 `fn(...)` 创建）
   - `safety`（用 `safety(scope, privacy, boundary)`）
   - `first_open`、`first_generated_function`
2. 在 [`scenarios.json`](./scenarios.json) 的 `scenarios` 里加一项，包含：
   - `file`（如 `running.json`）、`name`、`desc`
   - `category / daily_minutes / difficulty / audience`
   - `keywords`（搜索同义词，如「失眠」对应睡眠）
   - `icon`（Lucide 图标名，同时把图标存为 `assets/icons/<场景 slug>.svg`）
   - `featured`、`note`（非精选场景都填 `false` / `""`）
3. 在 `index.html` 的 `SCENARIOS` 数组里加一条展示信息（`file / name / desc / cat / min / diff`），字段需与 `scenarios.json` 一致。
4. 运行生成与校验：

   ```bash
   python3 scripts/generate_examples.py     # 中文场景 + examples/filled/
   python3 scripts/generate_en_examples.py  # 英文场景 examples/en/
   pip install jsonschema
   python3 scripts/validate.py
   ```

5. 在 `README.md` 的场景表里加一行（`scripts/validate.py` 会检查是否漏加）。
6. 如果想提供英文版，在 `scripts/generate_en_examples.py` 的 `SCENARIOS` 和 `META` 里加对应条目。英文场景使用 `form.en.json` 作为基础规范。

## 修改通用规则

通用流程、安全基线、存档格式在 `form.json` 里改。如果改动了存档结构：

1. 提升 `form.json` / `form.en.json` 的 `schema_version`。
2. 在 `updates.json` 的 `updates` 里加一条迁移，写清 `added_fields`、`renamed_fields`、`removed_fields`、`defaults`。
3. 同步两个模板里的 `compatibility.updates`（`current` 和 `migrations` 必须与 `updates.json` 一致）。
4. 重新生成并校验：

```bash
python3 scripts/generate_examples.py
python3 scripts/generate_en_examples.py
python3 scripts/validate.py
```

`scripts/validate.py` 会检查迁移清单与模板是否漂移、示例版本是否一致，以及 `scenarios.json` ↔ `examples/` ↔ `index.html` ↔ `README.md` 是否一致。

不要直接手改 `examples/*.json`、`examples/filled/*.json`、`examples/en/*.json`，它们由脚本生成，CI 会检查是否一致（启用方式见 [`docs/ci/README.md`](./docs/ci/README.md)）。

## 安全检查

提交前请确认：

- 不包含真实姓名、联系方式、证件号等个人信息
- 医疗、心理、法律、财务类场景保留了「非专业建议」边界
- 危机场景有明确的求助引导

## 提交

```bash
git checkout -b add-scenario-xxx
git add .
git commit -m "Add xxx scenario"
git push
```

然后开 Pull Request。
