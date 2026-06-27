---
name: okf-knowledge-base
description: >
  지식을 OKF(Open Knowledge Format) 형식으로 저장·갱신·검색할 때 사용한다.
  구체적으로 (1) 대화에서 나온 결론·절차·결정·참고자료를 ~/.claude/kb/ 에 정리/저장할 때,
  (2) 기존 KB 문서를 수정/갱신할 때, (3) KB에서 정보를 검색·참조할 때 이 스킬을
  로드하여 형식 규칙과 저장 위치 규칙, 안전 규칙을 따른다.
  AWS/DevOps 등 팀 지식 베이스를 다루는 모든 작업에 적용된다.
---

# OKF Knowledge Base Skill

## OKF란 (이름 의존 없는 자기완결 설명)
OKF는 지식을 "YAML 프론트매터가 붙은 마크다운 파일들의 디렉토리"로 표현하는
개방형 형식이다. 새 언어·런타임·SDK가 아니라, 아래 규칙을 따르는 평범한 마크다운
파일 모음이다. "OKF"라는 이름을 몰라도 이 문서의 규칙만 따르면 된다.

## 저장 위치 규칙
- KB 루트: `~/.claude/kb/`
  - `~/.claude/kb/common/` — 팀 공용 KB. **직접 수정·삭제 금지. 읽기(참조)만 허용.**
  - `~/.claude/kb/local/`  — 개인 로컬 KB. 모든 신규 저장의 기본 위치.
- 별도 지정이 없으면 저장은 항상 `~/.claude/kb/local/` 에 한다.
- common 보강 내용은 `~/.claude/kb/local/` 에 초안으로 저장 후, 사용자에게 승격(PR)을 안내한다.

## 핵심 개념
- 파일 하나 = 개념 하나.
- **파일 경로 = 개념 ID.** 예: `aws/standard-vpc.md` → `aws/standard-vpc`.
- 개념 간 관계는 마크다운 링크, 번들 루트 기준 **절대경로**(`/...`) 권장.

## 문서 구조
1. YAML 프론트매터 (`---` 구분)
   - 필수: `type`, `timestamp` (생성·최근 수정 시각, ISO 8601)
   - 권장: `title`, `description`, `resource`, `tags`
   - 신선도·생명주기: `verified-at` (원본과 마지막 대조 일자), `status` (`active`/`deprecated`), `superseded-by` (대체 문서 경로), `freshness-window` (대조 주기 일수, 미지정 시 기본 30)
2. 구조화된 마크다운 본문 (헤딩·표·리스트·코드블록 선호)
   - 관례 헤딩: `# Schema`, `# Examples`, `# Citations`
   - **Citations 는 "변질 의심 시 진위를 가리는 닻".** Reference/Decision 류는 사실상 필수.

## type 분류 (팀 컨벤션)
- `Reference` 서비스·리소스·구성 설명
- `Runbook`   장애·운영 대응 절차
- `HowTo`     재사용 가능한 작업 방법
- `Decision`  아키텍처·운영 결정 기록
- `Policy`    보안·IAM 등 정책
(모르는 type 도 거부하지 말고 일반 개념으로 처리.)

## 예약 파일
- `index.md` 디렉토리 목차(점진적 공개). 개념 문서 아님.
- `log.md`   변경 이력. 최신이 위, 날짜는 ISO 8601 (YYYY-MM-DD).
  - 이벤트 어휘: `Creation`(신규), `Update`(증분 갱신), `Correction`(오류 정정), `Verified-on`(원본과 대조 완료), `Deprecation`(폐기, `superseded-by` 와 함께).

## 검색·읽기 절차 (토큰 효율)
1. 먼저 `index.md` 로 무엇이 있는지 파악.
2. 프론트매터(type/title/description/tags)로 후보를 좁힘.
3. 관련 개념 문서만 선택적으로 연다 (lazy loading).
4. 번들 전체를 통째로 컨텍스트에 넣지 않는다.
5. **신선도 확인 (불변)**: 문서를 사용해 답변하기 전 `timestamp` / `verified-at` 가 `freshness-window` (미지정 시 30일)를 넘었으면 사용자에게 먼저 경고:
   > "이 문서는 N일 전 작성됐고 그 사이 실제 형상이 바뀌었을 수 있습니다."
   AI 가 의심을 띄우는 것이지, 사용자 인지에 의존하지 않는다.

## 저장·갱신 절차
모든 쓰기·갱신은 **단일 흐름**을 따른다: `AI 변경 diff 제시 → 사용자 승인 → 실행`.

1. 기본 저장 대상은 `~/.claude/kb/local/`. (common 직접 쓰기 금지)
2. 경로를 정한다(경로가 곧 개념 ID).
3. 같은 개념이 이미 있으면 **새로 만들지 말고 갱신**.
4. 변경 내용을 **diff 요약 + 출처(Citations)** 와 함께 사용자에게 제시하고 승인을 받는다.
   - "저장할까요?" 만 묻지 않는다. "이 3줄을 추가하고 표의 이 부분을 수정합니다. 저장할까요?" 처럼 **재료를 함께 준다.**
5. 승인 시에만 파일을 쓰고, `log.md` 에 이벤트(`Creation`/`Update`/`Correction`/`Deprecation`) 한 줄 기록.
6. 관련 개념은 절대경로 링크로 연결.
7. common 반영이 필요하면 local 초안 + 승격(PR) 안내.

## 안전 게이트 (불변)

### 관통 원칙
**사용자에게 묻되, 판단할 재료를 함께 줘라.**
"할까요/말까요" 만 묻는 것은 책임 떠넘기기. **diff · timestamp 경고 · 출처** 와 함께 물어야 실질적 게이트가 된다.

모든 위험 행위(쓰기 · 갱신 · 외부 조회) = **AI 제안 → 사용자 승인 → 실행**.

### 게이트 1 — Error Propagation (잘못된 내용이 KB로 흘러들어감)
- 트리거: 세션 종료 직전, 또는 지식성 결론이 KB 에 반영될 시점.
- AI: 무엇을 추가/수정하는지 **diff 요약 + 출처** 를 만들어 제시.
- 사용자: diff 검토 → 승인/거부/수정 지시.
- 결과: 승인 시에만 파일 쓰기 + `log.md` 한 줄.

### 게이트 2 — 갱신 충돌 (기존 개념에 변경 필요)
- 트리거: 같은 개념 ID 의 문서가 이미 있는데 새 변경이 발생.
- AI: 새 파일 만들지 말고 **기존 문서에 대한 변경 diff** 를 사용자에게 제시.
- 사용자: diff 검토 → 승인.
- 결과: 승인 시 파일 갱신 + `log.md` 에 변경 유형(`Update`/`Correction`/`Deprecation`) 기록.
- **게이트 1 과 동일 메커니즘** — `diff 제시 → 승인 → 커밋 + log.md`.

### 게이트 3 — Drift (문서와 실제 형상의 어긋남)
사용자 인지에 의존하지 않는다. **AI 가 의심을 먼저 띄우고, 검증 행위 자체도 사용자 승인을 받는다.**

승인 게이트가 **두 번** 있다.

1. **신선도 감지** — 문서 읽을 때 `timestamp` / `verified-at` 가 `freshness-window`(미지정 시 30일) 초과면 경고만 표시.
2. **대조 제안 (1차 게이트)** — "이 문서는 N일 전이고 `resource: <URI>` 가 있습니다. 원본과 대조해볼까요?" 라고 사용자에게 묻는다. **자동 대조 금지.**
3. **사용자 승인** — 승인 / 보류 / 거부.
4. **원본 조회** — 승인 시에만 `resource` URI 조회.
5. **결과 diff 제시 (2차 게이트)** — 차이가 있으면 KB ↔ 원본 diff 요약과 함께 "이 변경을 KB 에 반영할까요?" 묻기.
6. **사용자 승인** — diff 검토 후 승인.
7. **반영 + 기록** — 승인 시 파일 갱신 + `log.md` 에 `Correction` 또는 (차이 없을 때) `Verified-on` 기록. 후자의 경우 `verified-at` 도 오늘 날짜로 갱신.

### 게이트 요약표

| 행위 | 1차 게이트 | 2차 게이트 |
|---|---|---|
| 신규 저장 | diff + 출처 → "저장할까요?" | — |
| 갱신 | diff → "갱신할까요?" | — |
| 드리프트 검증 | timestamp 경고 → "대조할까요?" | 대조 diff → "반영할까요?" |

## 하지 말 것 (Anti-patterns)
- `~/.claude/kb/common/` 을 직접 수정·삭제하지 않는다.
- 대화 로그·채팅 전문을 통째로 한 파일에 붙여넣지 않는다. (정제된 지식만)
- `type` 없이 개념 문서를 저장하지 않는다.
- 대화 단위로 파일을 만들지 않는다. **주제(개념) 단위**로 만든다.
- 민감정보(시크릿/키/자격증명)를 본문에 넣지 않는다.
- 사용자 확인 없이 임의로 저장하지 않는다.
- **diff 요약 없이 "저장할까요?" 만 묻지 않는다.** (재료 없는 질문은 형식적 관문)
- **`resource` URI 등 외부 리소스를 사용자 승인 없이 조회하지 않는다.** (대조도 게이트를 거친다)
- 사용자의 "변질 인지" 를 기다리지 않는다. AI 가 timestamp 만료로 먼저 의심을 띄운다.

## 예시 1 — Reference (경로: ~/.claude/kb/local/aws/standard-vpc.md)
```markdown
---
type: Reference
title: 표준 VPC 구성
description: 팀 표준 VPC 네트워크 레이아웃과 서브넷 분리 원칙.
resource: https://console.aws.amazon.com/vpc/
tags: [aws, network, vpc]
timestamp: 2026-06-22T00:00:00Z
verified-at: 2026-06-22
status: active
---

# Overview
프로덕션 표준 VPC의 기본 레이아웃.

# Layout
| 구성요소        | 용도                          |
|---------------|-------------------------------|
| Public Subnet  | ALB, NAT Gateway             |
| Private Subnet | 애플리케이션 계층              |
| Data Subnet    | RDS 등 (외부 접근 차단)        |

# Related
- 배포는 [prod deploy](/runbooks/prod-deploy.md) 참조.

# Citations
[1] [AWS VPC 문서](https://docs.aws.amazon.com/vpc/)
```

## 예시 2 — Runbook (경로: ~/.claude/kb/local/runbooks/rds-failover.md)
```markdown
---
type: Runbook
title: RDS 장애 조치 대응
description: RDS Multi-AZ 장애 발생 시 대응 절차.
tags: [aws, rds, incident]
timestamp: 2026-06-22T00:00:00Z
---

# Symptoms
- 애플리케이션 DB 커넥션 타임아웃 급증.

# Steps
1. RDS 콘솔에서 인스턴스 상태/이벤트 확인.
2. Multi-AZ 자동 페일오버 진행 여부 확인.
3. 미진행 시 수동 페일오버 트리거.
4. 커넥션 풀 리셋 후 헬스체크 확인.

# Related
- 대상 DB는 [orders db](/aws/orders-db.md) 참조.
```

## 예시 3 — index.md / log.md
```markdown
# (index.md)
# AWS
* [표준 VPC 구성](aws/standard-vpc.md) - 팀 표준 VPC 레이아웃
# Runbooks
* [RDS 장애 조치](runbooks/rds-failover.md) - RDS 페일오버 대응
```
```markdown
# (log.md)
# Update Log
## 2026-06-25
* **Verified-on**: [표준 VPC 구성](/aws/standard-vpc.md) 콘솔과 대조, 차이 없음.
## 2026-06-23
* **Correction**: [표준 VPC 구성](/aws/standard-vpc.md) Data Subnet 설명 오류 정정.
## 2026-06-22
* **Creation**: [RDS 장애 조치](/runbooks/rds-failover.md) 추가.
```