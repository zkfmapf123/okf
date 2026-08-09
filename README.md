# okf — Open Knowledge Format for Claude Code

> [한국어](README.ko.md)

A Claude Code plugin that stores, updates, and searches knowledge as plain **YAML frontmatter + Markdown** files. No database, no embeddings — just files under `~/.claude/kb/`.

## Install

```text
/plugin marketplace add zkfmapf123/okf
/plugin install okf-knowledge-base@okf
```

## Usage

| Command | What it does |
|---|---|
| `/kb [question]` | Search the KB first, answer with sources. Falls back to a normal answer (marked `KB 없음`) if nothing matches. Tracks corrections and new knowledge during the follow-up conversation |
| `/kb-end` | End the current KB question. Hands tracked fixes/additions to the skill, which applies them after showing you a diff and getting approval |

The `okf-knowledge-base` skill also activates automatically when a conversation produces knowledge worth saving — it always asks with a diff before writing anything.

## How it works

- **Location**: `~/.claude/kb/local/` (yours) and `~/.claude/kb/common/` (team, read-only)
- **Format**: one file = one concept, path = concept ID
- **Safety**: every write goes through `diff → your approval → commit + log`; no secrets in files, `common/` is never modified directly
- **Freshness**: docs older than their `freshness-window` (default 30 days) trigger a warning before being used

Full format spec and examples: [`skills/okf-knowledge-base/SKILL.md`](skills/okf-knowledge-base/SKILL.md)

## License

MIT
