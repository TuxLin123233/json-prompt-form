#!/usr/bin/env python3
"""Validate form.json, examples/*.json, updates.json and template drift."""
import glob
import json
import os
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
