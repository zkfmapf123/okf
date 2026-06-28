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
   - 필수: `type`, `timestamp` (생성·최근 수정 시각, ISO 8601 정밀 시각 — 예: `2026-06-22T00:00:00Z`)
   - 권장: `title`, `description`, `resource`, `tags`
   - 신선도·생명주기:
     - `verified-at` — 원본과 마지막 대조 일자. ISO 8601 **날짜만** (예: `2026-06-22`)
     - `status` — `active` | `deprecated`
     - `superseded-by` — 대체 문서 경로 (Deprecation 시)
     - `freshness-window` — 대조 주기 **정수 일수** (예: `30`). 미지정 시 기본 30
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
- `index.md` 디렉토리 목차(점진적 공개). 개념 문서 아님. **각 디렉토리에 하나**.
- `log.md`   변경 이력. 최신이 위, 날짜는 ISO 8601 (YYYY-MM-DD).
  - **위치는 KB 루트 단일 파일** (`~/.claude/kb/local/log.md`). 하위 디렉토리에 별도로 두지 않는다.
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

0. **선행 — KB 디렉토리 부재 시**: `~/.claude/kb/local/` 또는 하위 디렉토리가 없으면, 게이트 (a) 카드의 `📂 index.md 동기화` 라인에 `+ mkdir -p <경로>` 를 함께 표시하고 사용자 승인 한 번에 같이 처리한다. 별도 게이트 아님.
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
- 트리거 (둘 중 하나):
  - (a) **사용자가 저장을 요청** (예: "이거 저장해줘", "KB 에 정리해줘")
  - (b) **AI 가 지식성 결론 발생을 감지해 자발 제안** (결정·절차·참고자료가 정리된 시점, 대화 중 또는 답변 직후)
  - ※ "세션 종료 직전" 은 Claude 가 관측 불가하므로 사용하지 않는다.
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

### diff 제시 표준 템플릿
모든 게이트에서 사용자에게 변경을 보여줄 때 아래 형식을 따른다. 일관된 검토 경험을 위해 매번 동일한 카드를 사용한다.

**응답 옵션은 항상 4개**: `승인 / 거부 / 수정 지시 / 보류`.

**(a) 신규 저장**
```
📄 신규: <KB-상대경로>
type: <type>
요약: <한 줄 설명>
출처(Citations): <URL 또는 "없음">

본문 요약:
- <섹션/표 헤딩>: <한 줄>
- ...

📂 index.md 동기화: + "[<title>](<path>)" 한 줄 추가

저장할까요?
```

**(b) 갱신 / 정정 / 폐기**
```
📄 갱신: <KB-상대경로>
변경 유형: Update | Correction | Deprecation
변경 규모: + N줄 / - M줄
이유: <왜 바꾸는지 / 무엇이 발견됐는지>
출처(Citations): <URL 또는 "없음">

핵심 diff:
+ <대표 추가 줄>
- <대표 삭제 줄>
(전체 diff 가 길면 "전체 보기" 옵션 제공)

📂 index.md 동기화: <필요 없음 | 항목 갱신 | 항목 제거>

갱신할까요?
```

**(c) 드리프트 검증 — 대조 제안 (1차 게이트)**
```
📄 신선도 경고: <KB-상대경로>
timestamp: <ISO 날짜>  (N일 전)
freshness-window: <N일 또는 기본 30>
resource: <URI>

원본과 대조할까요?
```

**(d) 드리프트 검증 — 대조 결과 (2차 게이트)**
```
📄 대조 결과: <KB-상대경로>
원본 vs KB:
+ <원본에는 있는데 KB 에 없음>
- <KB 에 있는데 원본에는 없음>
~ <서술이 달라진 부분>

(차이 없음이면: "✅ 일치. verified-at 만 오늘 날짜로 갱신할까요?")

KB 에 반영할까요?
```

### index.md 동기화 규칙
`index.md` 는 검색 절차의 1단계 진입점이라 항상 실제 파일 목록과 일치해야 한다.

- **신규 파일 생성** → 같은 게이트 흐름 안에서 해당 디렉토리 `index.md` 한 줄 추가 (별도 게이트 아님, 위 (a) 템플릿의 `📂 index.md 동기화` 라인으로 함께 승인).
- **`Correction` / `Update`** → 제목/설명이 바뀌었으면 `index.md` 항목 텍스트도 갱신, 안 바뀌었으면 동기화 불필요.
- **`Deprecation`** → 항목을 제거하거나, `superseded-by` 가 있으면 `~~<기존>~~ → [<후속>](path)` 형식으로 표시.
- **디렉토리 이동·이름 변경** → 출발지·도착지 양쪽 `index.md` 모두 동기화.
- **`index.md` 부재** → 해당 디렉토리에 첫 파일이 생성될 때 함께 생성한다.
- **공용 KB(`common/`)의 `index.md`** → 직접 수정 금지. local 초안 + 승격(PR) 안내로 대응.

## 읽기 모델 선택 (선택적 최적화)
기본 읽기는 Claude 가 직접 수행한다. 사용자가 토큰을 아끼고 싶을 때 로컬 `ollama` LLM 에 **본문 요약** 을 위임할 수 있다. 흐름은 단일 게이트 원칙 그대로 — **AI 가 묻고 사용자 승인 후 실행.**

### 불변 원칙
- **frontmatter 는 절대 위임하지 않는다.** Claude 가 raw 로 직접 읽는다. 안전 게이트 필드(`timestamp`, `verified-at`, `status`, `Citations`) 무결성 보장.
- **게이트 동작(저장·갱신·대조)에서는 호출 금지.** 정밀도 필수 → 항상 default 강제.
- **fallback 보장.** ollama 미설치 / 모델 부재 / 응답 실패 → 자동 default 회귀.
- **매번 묻는다.** 세션 단위 기억 없음.
- **ollama 모델이 0개면 질문 자체를 건너뛴다.** 곧바로 default 로 진행.
- **체크박스 질문은 `AskUserQuestion` 도구로 호출한다.** 인라인 텍스트 질문 금지.

### 도구 경로 해석
플러그인이 로컬 개발 / 마켓플레이스 설치 / 다른 위치 어디에 있든 Claude 는 다음 우선순위로 `okf_read.py` 경로를 해결한다. 세션 내 첫 호출 시 결정, 이후 재사용.
1. 환경 변수 `${CLAUDE_PLUGIN_ROOT}` 가 설정돼 있으면 → `${CLAUDE_PLUGIN_ROOT}/tools/okf_read.py`
2. 마켓플레이스 설치 캐시 → `~/.claude/plugins/cache/*/okf-knowledge-base/*/tools/okf_read.py` 중 가장 최신 버전 디렉토리. Bash 로:
   ```bash
   ls -t ~/.claude/plugins/cache/*/okf-knowledge-base/*/tools/okf_read.py 2>/dev/null | head -1
   ```
3. 로컬 개발 (현재 작업 디렉토리가 플러그인 repo 인 경우) → `./tools/okf_read.py`
4. 모두 실패 → 사용자에게 경로 안내 요청.

### 흐름
1. **사전 발견 (질문 없음)**: AI 가 먼저 `python <plugin-root>/tools/okf_read.py --list-models` 실행.
2. **분기**:
   - `ollama_alive: false` **또는** `available: []` → 묻지 말고 곧바로 Read tool 로 읽고 종료. (사용자에게 "ollama 모델이 없어 Claude 가 직접 읽습니다" 한 줄 통지 가능)
   - 모델 1개 이상 → 아래로 진행.
3. **게이트 1 — 위임 여부 (체크박스)**:
   ```
   📖 읽기: <경로>
   Ollama 로 위임할까요?
   ( ) 예    ( ) 아니오
   ```
4. **아니오** → Read tool 직접 사용, 종료.
5. **예** → **게이트 2 — 모델 선택 (체크박스)**:
   ```
   어느 모델로 읽을까요?
   ( ) qwen2.5:4b
   ( ) qwen2.5:8b
   ...
   ```
6. **읽기 실행**: `python <plugin-root>/tools/okf_read.py --read <path> --model <m>`.
7. **응답 사용**:
   - `model_used == "default"` → `body` 사용 (요약 안 됨)
   - 그 외 → `body_summary` 사용
   - `warning` 필드가 있으면 사용자에게 표시 (예: "ollama 호출 실패로 default 회귀")

### 도구: `tools/okf_read.py`
플러그인에 번들된 Python 스크립트. ollama 만 설치돼 있으면 별도 의존성 없음.

| 명령 | 출력 (JSON) |
|---|---|
| `--list-models` | `{"ollama_alive": bool, "available": [<model>...]}` |
| `--read <path>` | `{"frontmatter": "<raw>", "frontmatter_parsed": {...} \| null, "body": "<raw>", "model_used": "default"}` |
| `--read <path> --model <name>` | `{"frontmatter": "<raw>", "frontmatter_parsed": {...} \| null, "body_summary": "<요약>", "model_used": "<name>"}` 또는 실패 시 default 응답 + `warning` 필드 |

→ frontmatter 는 항상 raw 문자열 + 파싱된 dict 두 형태로 반환. 안전 게이트 필드(`timestamp`/`verified-at`/`freshness-window`/`resource`/`status`) 는 `frontmatter_parsed` 에서 직접 읽는다. 파싱 실패 시 `null` 이며, 이 경우 Claude 가 raw 를 직접 파싱한다.

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
- **신규 파일을 만들면서 `index.md` 동기화를 누락하지 않는다.** (인덱스가 stale 되면 검색 1단계가 깨짐)
- 매번 다른 형식으로 변경을 보여주지 않는다. 위 (a)~(d) 템플릿을 그대로 사용한다.
- **게이트 동작(저장/갱신/대조) 중에 ollama 읽기 위임을 호출하지 않는다.** (정밀도 필수)
- **frontmatter 를 ollama 에게 요약 위임하지 않는다.** (안전 게이트 필드 손실 위험)
- ollama 모델이 없는데도 굳이 사용자에게 "위임할까요?" 라고 묻지 않는다. 그 경우 곧바로 default 로 진행한다.

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