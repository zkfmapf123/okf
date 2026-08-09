# okf — Open Knowledge Format for Claude Code

> [English](README.md)

지식을 **YAML frontmatter + Markdown** 파일로 저장·갱신·검색하는 Claude Code 플러그인. DB도 임베딩도 없이 `~/.claude/kb/` 아래 파일만으로 동작합니다.

## 설치

```text
/plugin marketplace add zkfmapf123/okf
/plugin install okf-knowledge-base@okf
```

## 사용법

| 커맨드 | 동작 |
|---|---|
| `/kb [질문]` | KB 먼저 검색 후 근거와 함께 답변. 없으면 `KB 없음` 표시 후 일반 답변. 이후 대화의 지적·신규 지식을 추적 |
| `/kb-end` | 현재 KB 질문 종료. 추적된 수정/신규 건을 스킬에 넘기고, diff 확인 + 승인 후 반영 |

대화 중 저장할 만한 지식이 생기면 `okf-knowledge-base` 스킬이 자동으로 발동합니다 — 쓰기 전에 항상 diff 를 보여주고 승인을 받습니다.

## 동작 원리

- **위치**: `~/.claude/kb/local/` (개인), `~/.claude/kb/common/` (팀 공용, 읽기 전용)
- **형식**: 파일 하나 = 개념 하나, 경로 = 개념 ID
- **안전**: 모든 쓰기는 `diff 제시 → 사용자 승인 → 커밋 + log 기록` 흐름을 따름. 시크릿 저장 금지, `common/` 직접 수정 금지
- **신선도**: `freshness-window`(기본 30일) 지난 문서는 사용 전 경고

형식 상세와 예시: [`skills/okf-knowledge-base/SKILL.md`](skills/okf-knowledge-base/SKILL.md)

## 라이선스

MIT
