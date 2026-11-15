# CI 校验

`validate.yml` 是自动校验工作流：每次 push / PR 时运行 `scripts/validate.py`，并检查 `examples/` 是否与 `form.json` 保持一致。

## 为什么放在这里

GitHub 要求推送到 `.github/workflows/` 的 token 具备 `workflow` 权限。本项目当前使用的 token 只有 `repo` 权限，所以此文件先放在 `docs/ci/`。

## 如何启用

### 方式一：网页操作（最简单）

1. 打开仓库 → **Add file** → **Create new file**
2. 文件名填 `.github/workflows/validate.yml`
3. 把本目录 `validate.yml` 的内容粘贴进去
4. 提交

### 方式二：本地操作（需要 `workflow` 权限）

```bash
mkdir -p .github/workflows
cp docs/ci/validate.yml .github/workflows/validate.yml
git add .github/workflows/validate.yml
git commit -m "Enable CI validation"
git push
```

启用后，Actions 页面会出现 `Validate JSON` 工作流。
