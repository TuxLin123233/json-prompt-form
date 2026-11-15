# 🤖 json-prompt-form

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![JSON](https://img.shields.io/badge/format-JSON-blue.svg)](./form.json)
[![Stars](https://img.shields.io/github/stars/TuxLin123233/json-prompt-form?style=social)](https://github.com/TuxLin123233/json-prompt-form/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/TuxLin123233/json-prompt-form)](https://github.com/TuxLin123233/json-prompt-form/commits/main)

> 一个能「记住你」的 AI 助手模板。会复制粘贴，就能用。✨

## ✨ 这是什么？

把它想成一张**给 AI 的长期陪伴说明书**，外加一份**可以反复续上的存档**。

普通提示词聊完就忘；这个模板能让 AI 每次读你的存档，接着上次继续聊、继续帮你。

- 不用安装任何软件 🧰
- 不用会写代码 👌
- 打开网页版 AI（如 DeepSeek）就能用 💬

## 🚀 三步开始

**1️⃣ 选一个场景**
去 [`examples/`](./examples) 找一个最像你的；都不像就用 [`form.json`](./form.json)。

**2️⃣ 整份复制，发给 AI**
把选好的 JSON **全部内容**粘贴给 AI，再补一句你的真实情况。

**3️⃣ 聊完说「存档」**
AI 会给你一段 JSON，整段保存下来。下次开场贴「今天日期 + 存档」，就能接着来。

### 📋 照着复制就行

**第一次用：**
```
<把选好的 JSON 整份粘贴在这里>

今天是 2026-11-15。我的情况是：……（越具体越好）
```

**以后每次：**
```
今天是 2026-11-20。这是我的存档，请继续：
<把上次保存的 JSON 整段粘贴在这里>
```

**结束时：**
> 对 AI 说「存档」或「保存」，然后把回答里 ```` ```json ```` 代码块中的内容整段复制保存。

> 💡 小提醒：只复制代码块里的 JSON，不要复制 AI 的寒暄和解释。

## 🗂️ 文件说明

| 文件 | 是什么 |
| --- | --- |
| 📄 `form.json` | 通用模板，适合自定义场景 |
| 🎯 `examples/` | 六个现成场景，复制即用 |
| 🔍 `schema.json` | 可选：给懂技术的人检查存档格式，AI 用不到 |

## 🎯 六个现成场景

| 场景 | 文件 | 适合谁 |
| --- | --- | --- |
| 📚 备考 | [`study-exam.json`](./examples/study-exam.json) | 中高考、考研、考证，容易拖延焦虑 |
| 💪 健身 | [`fitness.json`](./examples/fitness.json) | 想增肌减脂塑形，但总坚持不下来 |
| 💼 求职 | [`job-search.json`](./examples/job-search.json) | 投简历没回音、面试紧张、求职焦虑 |
| 🌤️ 情绪支持 | [`emotion-support.json`](./examples/emotion-support.json) | 焦虑、低落、压力大，想有个出口 |
| 💰 财务 | [`finance.json`](./examples/finance.json) | 月光、超支、想存钱或还债 |
| ✍️ 写作 | [`writing.json`](./examples/writing.json) | 小说、公众号、日更，总卡文拖延 |

每个模板都会根据你的实际情况调整功能，也会在聊天中主动提议加新功能。

## 🧠 它怎么记住你？

1. AI 本身不记事，也看不到你的文件 📭
2. 所以每次由你把「存档」贴给它 📎
3. 聊完它把更新后的完整存档还给你，你保存好 💾

存档只在你手里，不上传、不联网、不依赖账号。

## 🛟 安全提醒

- 这是陪伴和自我管理工具，**不做医疗、心理、法律、投资等专业诊断** 🩺
- 遇到严重情绪危机，请第一时间联系当地急救/危机热线，或告诉身边可信任的人 🆘
- 存档可能包含你的隐私，请自己妥善保管 🔒

## 🔧 进阶：内部结构（给想改的人）

<details>
<summary>点开查看字段说明</summary>

| 字段 | 作用 |
| --- | --- |
| `schema_version` | 存档格式版本 |
| `usage` | 给 AI 的使用说明 |
| `goal` | 助手总目标 |
| `session_context` | 本次日期、贴入的存档、无记忆规则 |
| `compatibility` | 旧存档容错：缺字段补齐、未知字段保留 |
| `protocol` | 硬流程：首次 / 续接 / 会话中 / 收尾 |
| `assistant_identity` | 助手是什么、为什么存在、怎么陪伴 |
| `scene` | 用户要什么场景、为什么、怎么用 |
| `functions[]` | 功能列表 |
| `function_rules` | 功能生成、默认值、数量上限、过期检查 |
| `evolution` | 新增 / 调整 / 停用功能的演化规则 |
| `rejected_suggestions` | 被拒绝的提议及原因 |
| `memory` | 长期状态与近期会话摘要 |
| `safety` | 危机、隐私与专业边界 |
| `output_rules` | 语气、语言、一次一问、收尾格式 |
| `examples` | 各类对话示例 |

### 功能字段

```jsonc
{
  "id": "f_emotional_stability",   // f_ + 英文短名，创建后不变
  "name": "情绪稳定",
  "what": "是什么",
  "why": "为什么",
  "how": "怎么办",
  "trigger": "什么时候触发",
  "frequency": "每日 | 每周 | 按需 | 自定义（写明）",
  "linked_with": ["f_checkin"],    // 引用 id
  "status": "active",              // active | paused | retired
  "source": "initial",             // initial | ai_suggest | user_add | user_modify
  "last_triggered_at": null,
  "created_at": "2026-11-14",
  "updated_at": "2026-11-14"
}
```

### 可选校验

```bash
npx ajv-cli validate -s schema.json -d 存档.json
```

</details>

## 📄 License

[MIT](./LICENSE)
