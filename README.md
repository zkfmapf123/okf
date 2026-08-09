# okf — Open Knowledge Format for Claude Code

지식을 **YAML frontmatter + Markdown** 번들로 저장·갱신·검색하는 Claude Code 플러그인.
A Claude Code plugin to store, update, and search knowledge as YAML+Markdown bundles.

- 저장 위치: `~/.claude/kb/`
  - `common/` — 팀 공용 (읽기 전용, 직접 수정·삭제 금지)
  - `local/`  — 개인 로컬 (모든 신규 저장의 기본 위치)
- 형식: 파일 하나 = 개념 하나, 경로 = 개념 ID
- 안전: 시크릿/자격증명 본문 저장 금지

## Install (권장: 플러그인 마켓플레이스)

```text
/plugin marketplace add zkfmapf123/okf
/plugin install okf-knowledge-base@okf
```

설치 후 새 세션에서 `okf-knowledge-base` 스킬이 자동 활성화됩니다.

## Manual install (대안)

```bash
git clone https://github.com/zkfmapf123/okf.git ~/.claude/plugins/local/okf
ln -s ~/.claude/plugins/local/okf/skills/okf-knowledge-base \
      ~/.claude/skills/okf-knowledge-base
```

## Usage

대화 중 지식성 결론·절차·결정·참고자료가 나오면 스킬이 발동해 다음을 따릅니다.

| 동작 | 동작 위치 | 규칙 |
|---|---|---|
| 신규 저장 | `~/.claude/kb/local/` | `type` frontmatter 필수, 경로 = 개념 ID |
| 검색·참조 | `~/.claude/kb/common/` + `local/` | `index.md` → frontmatter → 본문 순서 |
| 수정 | `local/` 만 | 같은 개념이면 새로 만들지 말고 갱신, `log.md` 한 줄 기록 |

자세한 형식·예시는 [`skills/okf-knowledge-base/SKILL.md`](skills/okf-knowledge-base/SKILL.md) 참조.

### 슬래시 커맨드

| 커맨드 | 동작 |
|---|---|
| `/kb [질문]` | KB 먼저 검색 후 근거 기반 답변. 없으면 `KB 없음` 표시 후 일반 답변. 이후 대화의 KB 오류·신규 지식 후보를 추적 |
| `/kb-end` | 현재 KB 질문 종료. 추적된 수정/신규 후보를 스킬 게이트(diff+승인)로 넘겨 반영 |

## Layout

```
.
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── commands/
│   ├── kb.md          # /kb [질문] — KB 검색 후 답변
│   └── kb-end.md      # /kb-end   — 세션 종료, 수정/신규 후보를 스킬로 전달
├── skills/
│   └── okf-knowledge-base/
│       └── SKILL.md
├── tools/
│   └── okf_read.py    # ollama 읽기 위임 (선택)
├── CLAUDE.md
└── README.md
```

## License

MIT
