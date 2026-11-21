#!/usr/bin/env python3
"""把旧版 json-prompt-form 存档迁移到当前结构。

用法：
  python3 scripts/migrate.py archive.json -o migrated.json
  python3 scripts/migrate.py archive.json --in-place
  python3 scripts/migrate.py archive.json --compact -o compact.json

规则（与 updates.json 及模板内嵌的 compatibility.updates 保持一致）：
  - 按 updates.json 的 updates 从旧到新应用迁移：改名、补默认值、移除废弃字段。
  - 只补齐/改名，绝不覆盖用户已有数据；未知字段原样保留。
  - 缺失字段用当前 form.json 的默认值补齐。
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


def load_updates():
    path = os.path.join(ROOT, "updates.json")
    if not os.path.exists(path):
        return None
    return load(path)


def version_tuple(value):
    try:
        return tuple(int(part) for part in str(value).split("."))
    except (TypeError, ValueError):
        return (0, 0, 0)


def split_path(path):
    return [part for part in str(path).split(".") if part]


def get_path(obj, path):
    current = obj
    for part in split_path(path):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def set_path(obj, path, value):
    """Set a dotted path only when it is missing; never overwrite existing data."""
    parts = split_path(path)
    if not parts:
        return False
    current = obj
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        elif not isinstance(current[part], dict):
            return False
        current = current[part]
    if parts[-1] in current:
        return False
    current[parts[-1]] = copy.deepcopy(value)
    return True


def pop_path(obj, path):
    parts = split_path(path)
    if not parts:
        return False, None
    current = obj
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    if isinstance(current, dict) and parts[-1] in current:
        return True, current.pop(parts[-1])
    return False, None


def apply_updates(data, manifest, old_version, warnings):
    """Apply migration entries newer than old_version, oldest first."""
    applied = []
    for entry in sorted(
        manifest.get("updates", []), key=lambda item: version_tuple(item.get("version", "0.0.0"))
    ):
        version = entry.get("version")
        if not version or version_tuple(version) <= version_tuple(old_version):
            continue

        for rename in entry.get("renamed_fields", []):
            source, target = rename.get("from"), rename.get("to")
            if not source or not target or source == target:
                continue
            found, value = pop_path(data, source)
            if not found:
                continue
            if get_path(data, target)[0]:
                warnings.append("改名目标已存在，保留目标值：%s（旧值仍在 %s）" % (target, source))
                set_path(data, source, value)
            else:
                set_path(data, target, value)

        for path, value in entry.get("defaults", {}).items():
            set_path(data, path, value)

        for path in entry.get("removed_fields", []):
            found, _ = pop_path(data, path)
            if found:
                warnings.append("已移除废弃字段：%s" % path)

        applied.append(version)
    return applied


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


def nested_defaults(paths):
    root = {}
    for path, value in (paths or {}).items():
        set_path(root, path, value)
    return root


def normalize_date(value, field, warnings):
    if value in (None, ""):
        return None
    if isinstance(value, str) and DATE_RE.match(value):
        return value
    warnings.append("日期格式无效：%s = %r，已改为 null" % (field, value))
    return None


def normalize_functions(functions, defaults, warnings):
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
        for key, default in defaults.items():
            f.setdefault(key, copy.deepcopy(default))
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


def normalize_memory(memory, defaults, warnings):
    deep_fill(defaults, memory)
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
    manifest = load_updates()
    old_version = data.get("schema_version") or "1.0.0"
    if not data.get("schema_version"):
        warnings.append("未找到 schema_version，按 v1 处理")

    if manifest:
        current_version = manifest.get("current") or spec["schema_version"]
        policy = manifest.get("policy", {})
        if version_tuple(old_version) > version_tuple(current_version):
            warnings.append(
                "存档版本 %s 高于当前模板 %s，已跳过版本迁移并保留原版本号"
                % (old_version, current_version)
            )
            applied = []
            current_version = old_version
        else:
            applied = apply_updates(data, manifest, old_version, warnings)
    else:
        current_version = spec["schema_version"]
        policy = {}
        applied = []
        warnings.append("未找到 updates.json，仅按当前模板补齐字段")

    migrated = deep_fill(copy.deepcopy(spec), data)

    ctx = migrated.setdefault("session_context", {})
    ctx["today"] = normalize_date(ctx.get("today"), "session_context.today", warnings)
    ctx.setdefault("save_file", None)
    ctx.setdefault("rule", spec["session_context"]["rule"])
    ctx.setdefault("date_format", "所有日期使用 YYYY-MM-DD；未知用 null")

    function_defaults = {
        "name": "未命名功能",
        "what": "",
        "why": "",
        "how": "",
        "trigger": "按需",
        "frequency": "按需",
        "linked_with": [],
        "status": "active",
        "source": "initial",
        "last_triggered_at": None,
        "created_at": None,
        "updated_at": None,
    }
    function_defaults.update(spec.get("function_rules", {}).get("field_defaults", {}))
    function_defaults.update(policy.get("function_defaults", {}))

    memory_defaults = nested_defaults(
        policy.get("memory_defaults")
        or {
            "memory.state.global": {"mood_trend": [], "preferences": {}, "notes": ""},
            "memory.state.per_function": {},
            "memory.state.pending_signals": {},
            "memory.state.modified_suggestions": [],
            "memory.state.recent_sessions": [],
        }
    ).get("memory", {})

    migrated["schema_version"] = current_version
    migrated["functions"] = normalize_functions(
        migrated.get("functions"), function_defaults, warnings
    )
    migrated["memory"] = normalize_memory(
        migrated.setdefault("memory", {}), memory_defaults, warnings
    )
    if not isinstance(migrated.get("rejected_suggestions"), list):
        migrated["rejected_suggestions"] = []

    if compact:
        keep = spec["archive_modes"]["compact"]["must_keep"]
        migrated = {k: migrated[k] for k in keep if k in migrated}

    return migrated, old_version, applied, warnings


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
    migrated, old_version, applied, warnings = migrate(data, spec, args.compact)
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
            migrated.get("schema_version", spec["schema_version"]),
            len(migrated.get("functions", [])),
            "（精简）" if args.compact else "",
        ),
        file=sys.stderr,
    )
    if applied:
        print("已应用迁移：" + "、".join(applied), file=sys.stderr)
    for warning in warnings:
        print("提示：" + warning, file=sys.stderr)


if __name__ == "__main__":
    main()
