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
2. 在 `META` 里补上该场景的 `category / audience / daily_minutes / difficulty`。
3. 运行生成与校验：

   ```bash
   python3 scripts/generate_examples.py     # 中文场景 + examples/filled/
   python3 scripts/generate_en_examples.py  # 英文场景 examples/en/
   pip install jsonschema
   python3 scripts/validate.py
   ```

4. 在 `README.md` 和 `README.en.md` 的场景表里加一行。
5. 如果想提供英文版，在 `scripts/generate_en_examples.py` 的 `SCENARIOS` 和 `META` 里加对应条目。英文场景使用 `form.en.json` 作为基础规范。

## 修改通用规则

通用流程、安全基线、存档格式在 `form.json` 里改。改完记得重新生成所有示例：

```bash
python3 scripts/generate_examples.py
python3 scripts/validate.py
```

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
