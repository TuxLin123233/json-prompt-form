#!/usr/bin/env python3
"""把旧版 json-prompt-form 存档迁移到当前结构。

用法：
  python3 scripts/migrate.py archive.json -o migrated.json
  python3 scripts/migrate.py archive.json --in-place
  python3 scripts/migrate.py archive.json --compact -o compact.json

规则：
  - 缺失字段用当前 form.json 的默认值补齐，不覆盖用户已有数据。
  - 旧存档没有 schema_version 时按 v1 处理。
  - 功能缺少 id 时生成 f_xxx，并把 linked_with 里的功能名映射为 id。
  - 兼容日期格式：非 YYYY-MM-DD 的日期改为 null 并提示。
"""
import argparse
import copy
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID_RE = re.compile(r"^f_[a-z0-9_]+$")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def current_spec():
    return load(os.path.join(ROOT, "form.json"))


def slug(name, index):
    text = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
    return "f_" + (text or "func_%d" % (index + 1))


def deep_fill(defaults, value):
    """Recursively add keys missing from value; never overwrite existing data."""
    if isinstance(defaults, dict) and isinstance(value, dict):
        for key, default in defaults.items():
            if key not in value:
                value[key] = copy.deepcopy(default)
            else:
                value[key] = deep_fill(default, value[key])
        return value
    return value


def normalize_date(value, field, warnings):
    if value in (None, ""):
        return None
    if isinstance(value, str) and DATE_RE.match(value):
        return value
    warnings.append("日期格式无效：%s = %r，已改为 null" % (field, value))
    return None


def normalize_functions(functions, warnings):
    if not isinstance(functions, list):
        warnings.append("functions 不是数组，已重置为 []")
        return []
    functions = [f for f in functions if isinstance(f, dict)]
    name_to_id = {}
    for i, f in enumerate(functions):
        fid = f.get("id")
        if not fid or not isinstance(fid, str) or not ID_RE.match(fid):
            fid = slug(f.get("name", ""), i)
            base = fid
            n = 2
            used = {x.get("id") for x in functions if x is not f and isinstance(x.get("id"), str)}
            while fid in used:
                fid = "%s_%d" % (base, n)
                n += 1
            f["id"] = fid
            warnings.append("为功能「%s」生成 id：%s" % (f.get("name", "未命名"), fid))
        if f.get("name"):
            name_to_id[f["name"]] = f["id"]
    for f in functions:
        f.setdefault("name", "未命名功能")
        f.setdefault("what", "")
        f.setdefault("why", "")
        f.setdefault("how", "")
        f.setdefault("trigger", "按需")
        f.setdefault("frequency", "按需")
        if f.get("status") not in ("active", "paused", "retired"):
            if "status" in f:
                warnings.append("功能 %s 的 status 无效，已改为 active" % f["id"])
            f["status"] = "active"
        if f.get("source") not in ("initial", "ai_suggest", "user_add", "user_modify"):
            if "source" in f:
                warnings.append("功能 %s 的 source 无效，已改为 initial" % f["id"])
            f["source"] = "initial"
        linked = f.get("linked_with")
        if not isinstance(linked, list):
            linked = []
        f["linked_with"] = [name_to_id.get(x, x) for x in linked if isinstance(x, str)]
        for key in ("last_triggered_at", "created_at", "updated_at"):
            f[key] = normalize_date(f.get(key), "%s.%s" % (f["id"], key), warnings)
    return functions


def normalize_memory(memory, warnings):
    state = memory.setdefault("state", {})
    state.setdefault("global", {})
    state["global"].setdefault("mood_trend", [])
    state["global"].setdefault("preferences", {})
    state["global"].setdefault("notes", "")
    state.setdefault("per_function", {})
    state.setdefault("pending_signals", {})
    state.setdefault("modified_suggestions", [])
    state.setdefault("recent_sessions", [])
    sessions = state["recent_sessions"]
    if isinstance(sessions, list):
        for item in sessions:
            if isinstance(item, dict) and isinstance(item.get("summary"), str):
                if len(item["summary"]) > 120:
                    item["summary"] = item["summary"][:120]
                    warnings.append("recent_sessions 摘要超过 120 字，已截断")
    else:
        state["recent_sessions"] = []
    return memory


def migrate(data, spec, compact=False):
    warnings = []
    old_version = data.get("schema_version") or "1.0.0"
    if not data.get("schema_version"):
        warnings.append("未找到 schema_version，按 v1 处理")

    migrated = deep_fill(copy.deepcopy(spec), data)

    ctx = migrated.setdefault("session_context", {})
    ctx["today"] = normalize_date(ctx.get("today"), "session_context.today", warnings)
    ctx.setdefault("save_file", None)
    ctx.setdefault("rule", spec["session_context"]["rule"])
    ctx.setdefault("date_format", "所有日期使用 YYYY-MM-DD；未知用 null")

    migrated["schema_version"] = spec["schema_version"]
    migrated["functions"] = normalize_functions(migrated.get("functions"), warnings)
    migrated["memory"] = normalize_memory(migrated.setdefault("memory", {}), warnings)
    if not isinstance(migrated.get("rejected_suggestions"), list):
        migrated["rejected_suggestions"] = []

    if compact:
        keep = spec["archive_modes"]["compact"]["must_keep"]
        migrated = {k: migrated[k] for k in keep if k in migrated}

    return migrated, old_version, warnings


def main():
    parser = argparse.ArgumentParser(description="迁移 json-prompt-form 存档到当前结构")
    parser.add_argument("input", help="旧存档 JSON 路径")
    parser.add_argument("-o", "--output", help="输出路径；默认打印到 stdout")
    parser.add_argument("--in-place", action="store_true", help="覆盖原文件")
    parser.add_argument("--compact", action="store_true", help="输出精简存档")
    args = parser.parse_args()

    try:
        data = load(args.input)
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit("无法读取存档：%s" % exc)
    if not isinstance(data, dict):
        sys.exit("存档顶层必须是 JSON 对象")

    spec = current_spec()
    migrated, old_version, warnings = migrate(data, spec, args.compact)
    text = json.dumps(migrated, ensure_ascii=False, indent=4) + "\n"

    target = args.output or (args.input if args.in_place else None)
    if target:
        with open(target, "w", encoding="utf-8") as f:
            f.write(text)
        print("已写入 %s" % target)
    else:
        sys.stdout.write(text)

    print(
        "迁移完成：%s → %s，功能 %d 个%s"
        % (
            old_version,
            spec["schema_version"],
            len(migrated.get("functions", [])),
            "（精简）" if args.compact else "",
        ),
        file=sys.stderr,
    )
    for warning in warnings:
        print("提示：" + warning, file=sys.stderr)


if __name__ == "__main__":
    main()
