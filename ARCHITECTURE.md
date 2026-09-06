# ARCHITECTURE — okf 동작 구조

DB·임베딩·서버 없음. **마크다운 파일 + grep + 승인 게이트** 세 가지로만 동작한다.

## 1. 구성 요소

```
플러그인 (이 저장소)                         저장소 ~/.claude/kb/
├── CLAUDE.md          불변 원칙 (항상 로드)   ├── common/   팀 공용 · 읽기 전용
├── commands/kb.md     /kb  ──┐               └── local/    개인 · 모든 쓰기
├── commands/kb-end.md /kb-end┤                   ├── index.md   디렉토리별 목차
└── skills/.../SKILL.md ◄─────┘ 로드             ├── log.md     변경 이력 (루트 1개)
        │  형식·절차·게이트                        └── <dir>/*.md 개념 문서
        │
        ├── grep / read ─────────────────────► common/, local/
        └── write (승인 후에만) ───────────────► local/
```

| 요소 | 역할 |
|---|---|
| `CLAUDE.md` | 항상 로드. 저장 위치·저장 안 함 기본·안전 규칙만 |
| `commands/kb.md` | `/kb <질문>`. 검색 1회 → 답변 → 세션 추적 시작 |
| `commands/kb-end.md` | 누적된 fix/new 후보를 스킬 게이트로 넘김 |
| `SKILL.md` | 문서 형식, 검색·저장 절차, 승인 게이트, diff 카드 템플릿 |

## 2. 문서 형식 (파일 하나 = 개념 하나)

```
~/.claude/kb/local/aws/alb-timeout.md      ← 경로가 곧 개념 ID: /aws/alb-timeout
─────────────────────────────────────────
---
type: Reference                ← 필수. Reference|Runbook|HowTo|Decision|Policy
timestamp: 2026-08-26T…Z       ← 필수. 생성·수정 시각
title / description / resource ← 권장
tags: [aws, alb, 504]          ← 식별자. 정확 토큰 매치용
aliases: [504 왜 나, 타임아웃 순서]  ← 사용자 서술형 표현. 서술형 질문 히트용
related: [/aws/eks-alb-ingress]  ← 관련 개념 ID. 단방향, 1홉 확장용
verified-at / status / freshness-window ← 신선도
---
# 본문 (헤딩·표·코드블록)
# Citations   ← 출처. 변질 의심 시 진위 판별 닻
```

검색은 프론트매터가 담당하고 본문은 답변 근거로만 읽는다. 그래서 `tags`·`aliases`·`related` 품질이 검색 품질을 결정한다.

## 3. `/kb` 검색 흐름

```
/kb <질문>
  │
  ├─ grep -rilE "kw1|kw2|영문kw" ~/.claude/kb/   (1회. 파일명·프론트매터·본문 동시)
  │
  ├─ 히트 ──► 히트 파일 프론트매터 읽기 (tags / aliases / related)
  │            │
  │            ├─ related 로 1홉 이웃 확보 (본문은 안 엶)
  │            │
  │            ├─ timestamp / verified-at 가 freshness-window 초과?
  │            │     └─ 예 ──► ⚠ 신선도 경고 표시 (대조는 승인 후에만)
  │            │
  │            └─ 필요한 본문만 read ──► 근거 기반 답변 + "근거: <경로>"
  │
  └─ 미스 ──► index.md 1회 확인
               └─ "KB 없음" + 일반 지식 답변 ──► new 후보로 추적

  답변 끝:  KB-세션: fix … / new …   (누적 전체를 매번 다시 표시)
```

턴 최소화: grep 1회, 미스 시 index 1회. 디렉토리 순회·재탐색 없음. 500+ 파일에서도 호출 수 동일.

## 4. 세션 추적과 `/kb-end`

```
사용자                  /kb                        /kb-end (스킬 게이트)        ~/.claude/kb/local/
  │                      │                              │                          │
  ├─ /kb 질문 A ────────►│                              │                          │
  │◄── 답변 + KB-세션: new … ─┤                          │                          │
  │                      │                              │                          │
  ├─ "그거 틀렸어" ──────►│                              │                          │
  │◄── KB-세션: fix … / new … ┤                          │                          │
  │                      │                              │                          │
  ├─ /kb 질문 B ────────►│  (KB 없음이라 했는데 실제론 있었음)                        │
  │◄── KB-세션: fix <문서> aliases + "질문 표현" ┤       │                          │
  │                      │                              │                          │
  │        … 저장은 아직 안 함. 후보만 누적 …             │                          │
  │                      │                              │                          │
  ├─ /kb-end ───────────────────────────────────────────►│                          │
  │                      │                              ├─ 저장 전 grep 1회 ───────►│  (중복·related 후보)
  │◄── diff 카드 (a)/(b) + 출처 + related/aliases 제안 ──┤                          │
  ├─ 승인 / 거부 / 수정 지시 / 보류 ─────────────────────►│                          │
  │                      │                              ├─ 승인분만 write ─────────►│
  │                      │                              ├─ index.md 동기화 ────────►│
  │                      │                              └─ log.md 1줄 ─────────────►│
```

- 저장 트리거는 **사용자만** (`/kb-end`). AI 자동 저장 없음.
- `/kb-end` 없이 세션 끝나면 후보는 폐기. 의도된 설계 — 불필요한 저장 압박 방지.
- 미스 환류: "KB 없음"이었는데 있었으면 그 질문 표현을 `aliases`에 추가. 실제 질문 이력이 검색어가 됨.

## 5. 승인 게이트 (모든 쓰기·외부 조회)

```
게이트 1·2 — 신규 / 갱신 (1단)
  AI: diff 카드 + 출처 ──► 사용자 ──승인──► write + index.md + log.md

게이트 3 — 드리프트 (2단)
  timestamp 만료 감지
    └─ AI: "원본과 대조할까요?" ──► 사용자 ──승인──► resource URI 조회
                                                        └─ AI: KB ↔ 원본 diff ──► 사용자 ──승인──► Correction 반영
                                                                                                  또는 verified-at 갱신
```

원칙: **"할까요?" 단독 금지. diff·경고·출처를 재료로 같이 준다.** 응답 옵션은 항상 `승인 / 거부 / 수정 지시 / 보류`.

## 6. 파일 배치

```
~/.claude/kb/
├── common/            팀 공용. 직접 수정 금지 (승격 PR로만)
└── local/             개인. 모든 신규 저장
    ├── index.md       디렉토리 목차 (사람용, 검색 진입점 아님)
    ├── log.md         변경 이력. 최신 위. Creation/Update/Correction/Verified-on/Deprecation
    ├── aws/
    │   ├── index.md
    │   └── alb-timeout.md
    └── runbooks/
        ├── index.md
        └── host-oom-diagnosis.md
```

## 7. 설계 결정 요약

| 결정 | 이유 |
|---|---|
| grep만, 임베딩 없음 | 임베딩은 별도 모델 필수. 수천 파일까지는 프론트매터 랭킹으로 충분. 초과 시 aliases 그대로 벡터 메타로 재사용 가능 |
| 검색 진입은 수동 `/kb` | 자동 검색은 매 턴 비용. 훅으로 옮길 때도 읽기만 자동, 쓰기는 수동 유지 |
| 저장은 `/kb-end`에서 일괄 | 간단 질답까지 저장되는 오염 방지. 끝은 사용자가 정함 |
| `related` 프론트매터 단일화 | 본문 링크는 본문을 열어야 보임. 프론트매터면 1홉 확장이 헤더 읽기로 끝남 |
| `aliases` 는 예측이 아니라 환류로 채움 | 실제 미스에서 나온 표현이 진짜 검색어. 임베딩은 내 표현을 안 배우지만 aliases는 배움 |
