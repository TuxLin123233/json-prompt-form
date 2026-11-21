#!/usr/bin/env python3
"""Validate form.json, examples/*.json, updates.json and template drift."""
import glob
import json
import os
import re
import sys

try:
    import jsonschema
except ImportError:
    sys.exit("Missing dependency: pip install jsonschema")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = ("form.json", "form.en.json")
POLICY_BOOLS = ("never_overwrite_user_data", "keep_unknown_fields", "fill_missing_from_template")
POLICY_TEXT = ("on_resume", "announce", "function_id_rule", "date_rule")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def version_tuple(value):
    try:
        return tuple(int(part) for part in str(value).split("."))
    except (TypeError, ValueError):
        return (0, 0, 0)


def subschema(schema, name):
    return {
        "$schema": schema.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
        "$defs": schema["$defs"],
        "$ref": "#/$defs/" + name,
    }


def validate_with(schema, name, data):
    jsonschema.Draft202012Validator(subschema(schema, name)).validate(data)


def migration_payload(entry):
    return {
        "version": entry.get("version"),
        "added_fields": entry.get("added_fields"),
        "renamed_fields": entry.get("renamed_fields"),
        "removed_fields": entry.get("removed_fields"),
        "defaults": entry.get("defaults"),
    }


def check_manifest(manifest, errors):
    versions = [version_tuple(entry.get("version", "0.0.0")) for entry in manifest["updates"]]
    if versions != sorted(versions):
        errors.append("updates.json: updates 未按版本升序排列")
    if len(set(versions)) != len(versions):
        errors.append("updates.json: updates 存在重复版本")
    current = version_tuple(manifest["current"])
    for entry, version in zip(manifest["updates"], versions):
        if version > current:
            errors.append(
                "updates.json: 迁移版本 %s 高于 current %s"
                % (entry.get("version"), manifest["current"])
            )


def check_template(spec, manifest, rel, errors):
    prefix = rel + ": "
    if spec.get("schema_version") != manifest["current"]:
        errors.append(
            "%sschema_version=%r 与 updates.json current=%r 不一致"
            % (prefix, spec.get("schema_version"), manifest["current"])
        )

    embedded = spec.get("compatibility", {}).get("updates")
    if not isinstance(embedded, dict):
        errors.append(prefix + "缺少 compatibility.updates")
        return

    if embedded.get("current") != manifest["current"]:
        errors.append(prefix + "compatibility.updates.current 与 updates.json current 不一致")

    if [migration_payload(item) for item in embedded.get("migrations", [])] != [
        migration_payload(item) for item in manifest["updates"]
    ]:
        errors.append(prefix + "compatibility.updates.migrations 与 updates.json updates 不一致")

    policy = manifest["policy"]
    for key in POLICY_BOOLS:
        if embedded.get(key) != policy[key]:
            errors.append("%scompatibility.updates.%s 与 updates.json 不一致" % (prefix, key))
    for key in POLICY_TEXT:
        if not isinstance(embedded.get(key), str) or not embedded[key].strip():
            errors.append("%scompatibility.updates.%s 缺失或为空" % (prefix, key))
    if embedded.get("memory_defaults") != policy["memory_defaults"]:
        errors.append(prefix + "compatibility.updates.memory_defaults 与 updates.json 不一致")
    if set(embedded.get("function_defaults", {})) != set(policy["function_defaults"]):
        errors.append(prefix + "compatibility.updates.function_defaults 字段与 updates.json 不一致")



SCENARIO_FIELDS = {
    "file": str,
    "name": str,
    "desc": str,
    "category": str,
    "daily_minutes": int,
    "difficulty": str,
    "audience": str,
    "featured": bool,
    "note": str,
    "keywords": list,
    "icon": str,
}


def parse_index_scenarios(errors):
    path = os.path.join(ROOT, "index.html")
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        errors.append("index.html 读取失败：%s" % exc)
        return []
    if "const SCENARIOS = [" not in text:
        errors.append("index.html 中找不到 SCENARIOS 数组")
        return []

    block = text.split("const SCENARIOS = [", 1)[1].split("];", 1)[0]

    def text_field(chunk, key):
        match = re.search(r'%s:\s*"([^"]*)"' % key, chunk)
        return match.group(1) if match else None

    def int_field(chunk, key):
        match = re.search(r"%s:\s*(\d+)" % key, chunk)
        return int(match.group(1)) if match else None

    items = []
    for match in re.finditer(r'\{[^{}]*?file:\s*"([^"]+)"[^{}]*?\}', block):
        chunk = match.group(0)
        items.append({
            "file": match.group(1),
            "name": text_field(chunk, "name"),
            "desc": text_field(chunk, "desc"),
            "category": text_field(chunk, "cat"),
            "daily_minutes": int_field(chunk, "min"),
            "difficulty": text_field(chunk, "diff"),
            "featured": "featured: true" in chunk,
            "note": text_field(chunk, "note") or "",
        })
    return items


def check_scenarios(errors):
    path = os.path.join(ROOT, "scenarios.json")
    try:
        data = load(path)
    except (OSError, ValueError) as exc:
        errors.append("scenarios.json 读取失败：%s" % exc)
        return

    entries = data.get("scenarios")
    if not isinstance(entries, list) or not entries:
        errors.append("scenarios.json: scenarios 缺失或为空")
        return

    seen_files = set()
    seen_names = set()
    for index, entry in enumerate(entries, 1):
        label = "scenarios.json 第 %d 项" % index
        if not isinstance(entry, dict):
            errors.append(label + " 不是对象")
            continue
        for key, expected in SCENARIO_FIELDS.items():
            value = entry.get(key)
            if not isinstance(value, expected):
                errors.append("%s: %s 缺失或类型错误" % (label, key))
        keywords = entry.get("keywords")
        if isinstance(keywords, list) and (
            not keywords or not all(isinstance(k, str) and k.strip() for k in keywords)
        ):
            errors.append(label + ": keywords 必须是非空字符串数组")
        file = entry.get("file")
        name = entry.get("name")
        if not isinstance(file, str) or not file.endswith(".json"):
            errors.append(label + ": file 无效")
            continue
        if file in seen_files:
            errors.append("scenarios.json: 重复 file %s" % file)
        seen_files.add(file)
        if name in seen_names:
            errors.append("scenarios.json: 重复 name %s" % name)
        seen_names.add(name)

        for sub in ("", "filled"):
            target = os.path.join(ROOT, "examples", sub, file)
            if not os.path.exists(target):
                errors.append("scenarios.json: 缺少示例文件 examples/%s%s"
                              % (sub + "/" if sub else "", file))

        icon_path = os.path.join(ROOT, "assets", "icons", file.replace(".json", ".svg"))
        if not os.path.exists(icon_path):
            errors.append("scenarios.json: 缺少场景图标 assets/icons/%s.svg"
                          % file.replace(".json", ""))

        example_path = os.path.join(ROOT, "examples", file)
        if os.path.exists(example_path):
            meta = load(example_path).get("meta", {})
            for key in ("category", "audience", "daily_minutes", "difficulty"):
                if meta.get(key) != entry.get(key):
                    errors.append(
                        "scenarios.json 与 examples/%s 的 meta.%s 不一致：%r != %r"
                        % (file, key, entry.get(key), meta.get(key))
                    )

    example_files = {
        os.path.basename(path)
        for path in glob.glob(os.path.join(ROOT, "examples", "*.json"))
    }
    filled_files = {
        os.path.basename(path)
        for path in glob.glob(os.path.join(ROOT, "examples", "filled", "*.json"))
    }
    for missing in sorted(example_files - seen_files):
        errors.append("examples/ 中有未收录到 scenarios.json 的场景：%s" % missing)
    for missing in sorted(filled_files - seen_files):
        errors.append("examples/filled/ 中有未收录到 scenarios.json 的场景：%s" % missing)

    index_items = parse_index_scenarios(errors)
    if index_items:
        if len(index_items) != len(entries):
            errors.append(
                "index.html 场景数 %d 与 scenarios.json %d 不一致"
                % (len(index_items), len(entries))
            )
        by_file = {entry["file"]: entry for entry in entries if isinstance(entry, dict)}
        for item in index_items:
            entry = by_file.get(item["file"])
            if entry is None:
                errors.append("index.html 引用了未收录的场景：%s" % item["file"])
                continue
            for index_key, scenario_key in (
                ("name", "name"),
                ("desc", "desc"),
                ("category", "category"),
                ("daily_minutes", "daily_minutes"),
                ("difficulty", "difficulty"),
                ("featured", "featured"),
                ("note", "note"),
            ):
                if item[index_key] != entry.get(scenario_key):
                    errors.append(
                        "index.html 的 %s 字段 %s 与 scenarios.json 不一致：%r != %r"
                        % (item["file"], index_key, item[index_key], entry.get(scenario_key))
                    )

    readme_path = os.path.join(ROOT, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, encoding="utf-8") as f:
            readme = f.read()
        for file in sorted(seen_files):
            if "examples/" + file not in readme:
                errors.append("README.md 场景表缺少 examples/%s" % file)


def main():
    schema = load(os.path.join(ROOT, "schema.json"))
    updates = load(os.path.join(ROOT, "updates.json"))
    errors = []

    archive_paths = [
        os.path.join(ROOT, "form.json"),
        os.path.join(ROOT, "form.en.json"),
    ] + sorted(
        glob.glob(os.path.join(ROOT, "examples", "**", "*.json"), recursive=True)
    )

    failed = False
    for path in archive_paths:
        rel = os.path.relpath(path, ROOT)
        try:
            jsonschema.validate(load(path), schema)
            print("OK   " + rel)
        except jsonschema.ValidationError as exc:
            failed = True
            print("FAIL " + rel + ": " + exc.message)

    try:
        validate_with(schema, "update_manifest", updates)
        print("OK   updates.json")
    except jsonschema.ValidationError as exc:
        failed = True
        print("FAIL updates.json: " + exc.message)

    if not failed:
        check_manifest(updates, errors)
        for rel in TEMPLATES:
            spec = load(os.path.join(ROOT, rel))
            try:
                validate_with(
                    schema, "embedded_updates", spec.get("compatibility", {}).get("updates")
                )
            except jsonschema.ValidationError as exc:
                errors.append("%s: compatibility.updates 无效：%s" % (rel, exc.message))
                continue
            check_template(spec, updates, rel, errors)

        for path in archive_paths[2:]:
            rel = os.path.relpath(path, ROOT)
            version = load(path).get("schema_version")
            if version != updates["current"]:
                errors.append(
                    "%s: schema_version=%r，应为 %r（请重新运行生成脚本）"
                    % (rel, version, updates["current"])
                )

    scenario_errors = []
    check_scenarios(scenario_errors)
    errors.extend(scenario_errors)

    for message in errors:
        print("FAIL " + message)
    if failed or errors:
        return 1
    print("\nAll valid: %d archive files, updates.json, %d templates" % (
        len(archive_paths),
        len(TEMPLATES),
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
