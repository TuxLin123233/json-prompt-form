# json-prompt-form

Json 驱动的提示词表单。

一份用 JSON 描述「长期陪伴式 AI 助手」的提示词规范：把助手的身份、场景、功能、演化规则和记忆全部结构化进 `form.json`，让 AI 按这份表单为用户生成并持续陪同一个可成长的助手。

## 它解决什么问题

普通提示词是一次性的，聊完就忘。本项目用两个 JSON 字段实现了「跨会话的长期陪伴」：

- `session_context`：用户每次开场贴入上次保存的存档 JSON，AI 以存档为唯一历史，不假装记得；
- `memory` + `functions`：所有状态写入存档，会话结束时 AI 输出更新后的完整 JSON，用户自行保存，下次续接。

## 文件

```
form.json    提示词表单规范本体
```

## 使用方式

1. 打开 `form.json`，整份内容作为系统提示 / 开场上下文发给 AI（网页版对话即可）。
2. **首次使用**：告诉 AI 今天的日期和你的场景、痛点，AI 会确认 `assistant_identity` / `scene`，自动生成 3–8 个 `functions` 让你确认，最后输出完整存档 JSON。把这份 JSON 保存下来。
3. **后续续接**：开场贴入今天日期 + 上次保存的存档 JSON，AI 会先做 `stale_check`，再按功能继续陪伴。
4. **会话结束**：AI 输出更新后的完整存档 JSON，覆盖保存即可。

参考 `examples` 字段里的示例：首次开场、续接开场、功能诞生、功能过期提醒、AI 主动提议等。

## 结构说明

| 字段 | 作用 |
| --- | --- |
| `goal` | 助手的总目标：生成并长期陪同一个助手 |
| `session_context` | 每次会话的上下文（今天日期、贴入的存档、无记忆规则） |
| `assistant_identity` | 助手是什么、为什么存在、以什么姿态陪伴 |
| `scene` | 用户要什么场景、为什么、怎么用 |
| `functions[]` | 功能列表，每个含 `what/why/how/trigger/frequency` 等 |
| `function_rules` | 功能生成规则与 30 天未使用的过期检查 |
| `evolution` | 功能演化：AI 如何提议新增 / 调整 / 停用，以及接受后的写入规则 |
| `rejected_suggestions` | 被拒绝的提议及原因 |
| `memory` | 长期状态（进度、情绪、偏好），结束时写入存档 |
| `output_rules` | 语气、一次只问一个问题、收尾输出存档 JSON |
| `examples` | 各类场景的示例，供 AI 对齐行为 |

## 功能字段

```jsonc
{
  "name": "功能名",
  "what": "是什么",
  "why": "为什么",
  "how": "怎么办",
  "trigger": "什么时候触发",
  "frequency": "每日/每周/按需",
  "linked_with": ["关联功能名"],
  "status": "active",
  "source": "initial | ai_suggest | user_add",
  "last_triggered_at": null,
  "created_at": null,
  "updated_at": null
}
```

## 设计原则

- **无跨会话记忆**：AI 不假设自己记得上次对话，历史只认用户贴入的存档。
- **功能可演化**：同一需求出现 ≥2 次或用户明确表达缺失时，AI 提议新增 / 调整 / 停用，由用户决定。
- **持久化靠用户**：演化结果不自动保存，必须由会话结束时输出的存档 JSON 手动落盘。
- **无定时唤醒**：网页版无法主动定时，过期检查只在开场贴入存档时执行一次。

## License

[MIT](./LICENSE)
