# 모듈 2 · 컨텍스트 엔지니어링 및 성능 최적화 (심화 학습 가이드)

> Building Advanced Agentic Systems on AWS (한국어) · 300레벨 심화
> 원본 강사 덱: `MLADAS-10-KO-KR-M02-ContextEngineering_InstructorDeck.pptx` (총 54개 슬라이드)
> 슬라이드 전사본을 아래 4가지 관점으로 재구성했습니다. 원본 슬라이드 전사본은 `_slide-transcript-backup/`에 보관되어 있습니다.
>
> **① 문제 해결에 고려할 기술·서비스·기능 → ② 구현 요건·절차 → ③ 구현 예시 → ④ 모범 사례(Well-Architected Agentic AI Lens 통합)**

---

## 학습 목표 및 선수 지식

**이 모듈을 마치면 다음을 수행할 수 있습니다.**
- 컨텍스트를 유한한 리소스로 진단하고, 토큰 예산·실패 모드·비용을 정량적으로 분석한다.
- 5대 컨텍스트 최적화 전략(입력 형식·기록·선택·압축·분리)을 선택·조합·구현한다.
- Amazon Bedrock 프롬프트 캐싱과 정적 요소 우선 구조로 지연·비용을 함께 낮춘다.
- 정보 집약형 도구·MCP 중앙 집중화·시맨틱 도구 검색으로 도구 계층의 컨텍스트 효율을 극대화한다.
- 각 결정을 Well-Architected Agentic AI Lens 모범 사례(성능·비용 기둥 중심)에 근거해 검증한다.

**선수 지식**: 모듈 1(다중 에이전트·AgentCore Memory·Strands), LLM 토큰·컨텍스트 윈도우 개념, RAG 기초, Amazon Bedrock 모델(Claude·Nova) 기초.

---

## 모듈 개요 — 이 모듈이 푸는 3가지 문제

컨텍스트 엔지니어링은 개별 프롬프트를 작성하는 일이 아니라 **에이전트가 작동하는 전체 정보 환경을 설계**하는 일입니다. 프로토타입과 프로덕션을 가르는 결정적 차별화 요소이며, 결국 세 가지 질문에 답하는 과정입니다.

| 파트 | 핵심 질문 | 산출물 |
| --- | --- | --- |
| 1. 문제 진단 | 컨텍스트는 *왜* 유한하고 비싼 리소스인가? | 토큰 예산·실패 모드 진단 프레임워크 |
| 2. 최적화 전략 | 유한한 컨텍스트를 *어떻게* 최적화하는가? | 5대 전략(입력 형식·기록·선택·압축·분리) |
| 3. 프롬프트 캐싱 | 반복되는 정적 컨텍스트를 *어떻게* 재사용하는가? | 정적 우선 구조·캐시 체크포인트 |
| 4. 도구 설계 | 도구 계층에서 컨텍스트를 *어떻게* 아끼는가? | 정보 집약형·중앙 집중·집중형 도구 |

> **AI 엔지니어링의 진화(전제)**: 프롬프트 엔지니어링 → RAG(지식 추가) → 에이전트(도구·자율성) → **컨텍스트 엔지니어링(대규모 프로덕션)**. 각 단계는 이전을 대체하지 않고 그 위에 쌓입니다. 기능이 늘수록 복잡성도 커지며, 이 복잡성을 엔터프라이즈 규모에서 관리해 측정 가능한 ROI를 만드는 것이 컨텍스트 엔지니어링입니다. 모듈 1이 *에이전트를 어떻게 나누는가*였다면, 이 모듈은 *나눈 에이전트에게 무엇을 얼마나 넣어줄 것인가*를 다룹니다.

---

## 파트 1. 컨텍스트는 유한한 리소스다 — 문제 진단과 토큰 경제학

### 1.1 해결할 문제

에이전틱 시스템에서 **컨텍스트란 각 요청과 함께 언어 모델로 전송되는 메시지 배열(messages)에 담긴 모든 것**입니다. 상호작용이 일어날 때마다 사용자 입력·어시스턴트 응답·도구 호출·도구 결과가 배열에 누적됩니다. 자율 에이전트 루프에서는 에이전트가 문제를 파악하고 도구를 호출하고 결과를 처리하는 동안 이 배열이 빠르게 부풀어 오릅니다.

문제는 컨텍스트 윈도우가 **유한하고, 매 요청마다 토큰을 소비하며, 커질수록 느려지고 품질이 떨어진다**는 데 있습니다. 세 가지 구조적 압력이 동시에 작용합니다.

- **용량 압력**: 컨텍스트 윈도우는 단일 상호작용에서 처리 가능한 최대 정보량을 정의하는 고정 한계입니다. 기존 애플리케이션처럼 "메모리를 더 붙이는" 식으로 확장할 수 없습니다.
- **비용 압력**: 모든 요청은 입력·출력 토큰 모두에 과금됩니다. 참조되지 않는 컨텍스트도 컨텍스트 윈도우에 실려 있는 한 매번 비용을 발생시킵니다.
- **품질 압력**: 컨텍스트가 커지면 "Lost in the Middle"(중간 정보 소실), 우선순위 경합, 처리 지연이 심해집니다. 윈도우를 키운다고 자동으로 해결되지 않습니다.

> **💡 팁 — 범위 설정**: 컨텍스트 엔지니어링을 프롬프트 엔지니어링보다 넓은 분야로 먼저 자리매김하세요. "LLM이 정확히 알아야 하는 상황 정보는 무엇인가?"를 물으면, 학습자는 프롬프트 한 줄이 아니라 시스템·검색·도구·메모리·사용자가 얽힌 *정보 환경*을 떠올리게 됩니다. 간단한 메시지 배열 예제로 토큰이 실시간으로 누적되는 모습을 시연한 뒤 자율 루프로 확장하면 이해가 빠릅니다.

#### 🧪 실습 — 메시지 배열 토큰 누적 시연

아래 코드는 에이전트 루프에서 `messages` 배열에 메시지가 쌓이며 토큰이 실시간으로 누적되는 모습을 출력합니다. 한 번의 사용자 문의가 여러 메시지(`user`→`assistant`→`tool_use`→`tool_result`)를 추가하고, 토큰은 줄지 않고 **커지기만 한다**는 점을 눈으로 확인할 수 있습니다. (의존성 없이 실행되며, `pip install tiktoken` 시 더 정확한 토큰 수를 보여줍니다.)

```python
"""컨텍스트 누적 시연 — messages 배열에 메시지가 쌓이며 토큰이 실시간 누적되는 모습."""

# --- 토큰 카운터: tiktoken이 있으면 사용, 없으면 근사(개념 시연용) ---
try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")   # 참고용(실제 Claude/Nova 토크나이저와는 다름)
    def count_tokens(text: str) -> int:
        return len(_enc.encode(text))
except ImportError:
    def count_tokens(text: str) -> int:
        return max(1, len(text) // 4)             # 근사: 영어 ≈ 4자/토큰 (한국어는 더 높음)

CONTEXT_WINDOW = 200_000   # 모델 컨텍스트 윈도우 상한(예: Claude 200K). 8000처럼 낮추면 막대가 빨리 참
RESPONSE_BUFFER = 5_000    # 응답 생성용으로 남겨둘 버퍼

def total_tokens(messages: list[dict]) -> int:
    """메시지 배열 '전체'의 누적 토큰 수(매 요청 전체가 다시 전송되므로 합산)."""
    return sum(count_tokens(str(m["content"])) for m in messages)

def show(messages: list[dict], label: str) -> None:
    """현재 메시지 수·누적 토큰·사용률 막대를 한 줄로 출력한다."""
    used = total_tokens(messages)
    usable = CONTEXT_WINDOW - RESPONSE_BUFFER
    pct = used / usable * 100
    filled = min(20, int(pct // 5))               # 막대가 20칸을 넘지 않도록 상한
    bar = "█" * filled + "·" * (20 - filled)
    print(f"[{label:<14}] 메시지 {len(messages):>2}개 | 누적 {used:>7,} 토큰 | {bar} {pct:5.1f}%")

# 시스템 지침(정적)으로 시작
messages = [{"role": "system", "content": "You are a helpful support agent. " * 400}]
show(messages, "시스템 로드")

# 핵심: 사용자 1회 문의가 실제로는 여러 메시지를 배열에 추가한다.
turns = [
    ("user",        "주문 45678이 아직 안 왔어요."),
    ("assistant",   "주문 상태를 조회하겠습니다."),                    # 추론/응답
    ("tool_use",    "get_order_status(order_id='45678')"),           # 도구 호출
    ("tool_result", "에러 로그: connection timeout at service-a\n" * 2000),  # 대용량 도구 결과(로그)
    ("assistant",   "배송 중이며 2일 내 도착 예정입니다."),
    ("user",        "방수되는 다른 모델도 추천해 주세요."),
    ("tool_use",    "search_products(query='방수 카메라')"),
    ("tool_result", "제품: AquaPro 200 | 방수 10m | ...\n" * 2500),   # 검색 결과 누적
    ("assistant",   "방수 모델로 AquaPro 200을 추천드립니다."),
]

for role, content in turns:
    messages.append({"role": role, "content": content})   # 메시지 추가
    show(messages, f"+{role}")                            # 추가될 때마다 누적 토큰이 '커지기만' 한다

# 한계 근접 경고
if total_tokens(messages) > (CONTEXT_WINDOW - RESPONSE_BUFFER) * 0.8:
    print("\n[경고] 사용 가능 컨텍스트의 80% 초과 → 최적화(기록·선택·압축) 필요 지점")
```

> **💡 시연 포인트**: ① **한 턴 = 여러 메시지**(`user` 하나가 `assistant`·`tool_use`·`tool_result`까지 추가). ② LLM은 상태가 없어(stateless) 매 요청마다 배열 *전체*를 재전송하므로 토큰은 **누적만** 된다. ③ `tool_result`(로그·검색 결과)에서 토큰이 급증 → 파트 2의 압축·선택 전략 필요성으로 자연스럽게 연결된다. `CONTEXT_WINDOW`를 8000처럼 낮추면 막대가 빠르게 차 더 극적입니다. 프로덕션 정확 측정은 Bedrock 응답의 `usage`나 Strands `response.metrics.accumulated_usage`를 사용합니다.

### 1.2 고려해야 할 개념 — 컨텍스트 5범주·윈도우·4대 실패 모드

#### (1) 컨텍스트 5범주 — 진단 프레임워크

에이전틱 컨텍스트는 보통 5가지 범주로 나뉩니다. 각 범주는 용도가 다르고 최적화 접근도 다르며, **동시에 에이전트 실패를 진단하는 프레임워크**로 기능합니다.

| 범주 | 역할 | 주요 출처 | 전형적 실패 증상 | 주로 발생하는 상황(원인) |
| --- | --- | --- | --- | --- |
| **시스템** | 역할·행동 지침 | 시스템 프롬프트 | 일관되지 않은 행동, 제약 무시 | 컨텍스트 누적으로 지침 비중 희석·최근성 편향·후속 컨텍스트와 충돌 |
| **검색됨** | 외부 지식 | RAG · Amazon Bedrock Knowledge Bases | 잘못된 정보, 오래된 데이터, 무관한 결과 | 검색 품질 저하·오래된 인덱스·무관 청크 과다 주입 |
| **도구** | 사용 가능한 기능 | API 연결 · MCP 도구 | 잘못된 도구 선택, 잘못된 파라미터 | 도구 수 과다·모호한 도구 설명·기능 중복 |
| **메모리** | 연속성 | AgentCore Memory(단기·장기) | 중요 정보 망각, 무관 데이터 유지 | 요약 시 정보 손실·부정확한 검색·세션 격리 미흡 |
| **사용자** | 현재 상호작용 | 프롬프트·프로필·자격 증명 | 멀티테넌트에서 프로필·자격 증명 혼동 | 동시 세션에서 actor/세션 ID 격리 미흡·프로필 주입 오류 |

*증상*은 어느 범주의 문제인지, *상황(원인)*은 왜 생겼는지를 가리킵니다. 대부분의 실패는 소스가 많아지고 대화가 누적되며 각 신호(특히 맨 앞의 시스템 지침)의 상대적 비중이 줄거나(희석) 신호 간 충돌·최근성 편향이 커질 때 두드러집니다(→ 파트 1.4 성능 저하, 파트 2 압축·선택 전략으로 대응).

> **💡 팁**: 에이전트가 오작동할 때 "어느 범주의 컨텍스트 문제인가?"를 먼저 물으면 디버깅이 체계화됩니다. 일관되지 않은 행동 → 시스템, 헛소리 → 검색됨, 엉뚱한 도구 → 도구, 앞 내용을 잊음 → 메모리, 사용자 혼동 → 사용자.

#### (2) 컨텍스트 윈도우 — 유한 리소스의 실체

컨텍스트 윈도우는 인간의 작업 기억(working memory)과 같습니다. 한 번에 붙잡고 있을 수 있는 정보량에 물리적 상한이 있고, 그 상한을 넘기면 앞의 것을 놓칩니다. 5개 범주의 컨텍스트 소스는 **컨텍스트 관리(최적화) 계층**을 거쳐 LLM 컨텍스트 윈도우로 주입됩니다. 이 관리 계층을 어떻게 설계하느냐가 파트 2~4의 주제입니다.

```ascii
┌─ 컨텍스트 소스 (5범주)
│
├─ 시스템
├─ 검색됨
├─ 도구
├─ 메모리
├─ 사용자
│
│  원시 컨텍스트
v
┌─ 컨텍스트 관리 계층
│  입력 형식 / 기록 / 선택 / 압축 / 분리
│
│  최적화된 컨텍스트만 주입
v
┌─ LLM 컨텍스트 윈도우
└─ 유한 토큰 / 매 요청 과금
```

#### (3) 4대 컨텍스트 실패 모드

컨텍스트를 잘못 관리하면 에이전트 성능을 심각하게 훼손하는 4가지 실패 모드가 나타납니다.

| 실패 모드 | 정의 | 예시 |
| --- | --- | --- |
| **포이즈닝(Poisoning)** | 불완전·오해 소지 컨텍스트에서 잘못된 가정을 구축 | 잘린 문서에 기능이 없다는 이유로 "그 기능은 없다"고 단정 |
| **주의 분산(Distraction)** | 과도한 컨텍스트로 주요 목표에 집중 실패 | 문제 해결 중 무관한 과거 정보에 주의를 뺏김 |
| **혼동(Confusion)** | 무관한 콘텐츠가 부적절한 도구 호출 유발 | 가상 토론 중 실제 환불을 시도 |
| **충돌(Clash)** | 모순 지침이 의사결정을 방해 | "항상 도와라" + "절대 환불 금지"가 공존 |

> **💡 팁**: 각 실패 모드를 문제성 컨텍스트가 담긴 라이브 에이전트로 시연하면 강렬합니다. 포이즈닝은 특히 컨텍스트 품질(신뢰성)과 직결되므로, 검색·메모리 파이프라인의 데이터 검증과 연결해 설명하세요.

### 1.3 구현 요건 및 절차 — 토큰 예산화와 진단

컨텍스트를 유한 리소스로 다루는 첫걸음은 **토큰 예산(token budget)을 명시적으로 배분**하는 것입니다. 다음 절차를 따릅니다.

1. **윈도우 상한 확인**: 사용 모델의 컨텍스트 윈도우 크기를 확인한다(예: 200,000 토큰).
2. **응답 버퍼 예약**: 에이전트가 응답을 생성할 여유 토큰을 먼저 떼어 둔다(예: 5,000 토큰). 이 버퍼를 침범하면 응답이 잘린다.
3. **범주별 예산 배분**: 남은 예산을 5범주에 배분하고, 각 구성 요소가 예산에 *얼마나* 기여하는지 정량화한다.
4. **누적 시뮬레이션**: 대화가 20~30턴 이어질 때 어느 범주가 먼저 예산을 잠식하는지 시뮬레이션한다(보통 메모리·검색됨).
5. **실패 모드 사전 점검**: 각 범주에 대해 4대 실패 모드 중 무엇이 발생 가능한지 점검하고 대응(검증·필터·우선순위)을 설계한다.

### 1.4 구현 예시 — 고객 서비스 에이전트의 200K 토큰 예산

한 고객 서비스 AI 에이전트가 **200,000 토큰 컨텍스트 윈도우**에서 복잡한 기술 문의를 해결한다고 합시다. 컨텍스트는 전략적으로 배분됩니다.

```ascii
┌─ 토큰 배분 상세
│
├─ 토큰 75,000개 -- 검색됨 (RAG 사전 검색)
│    - 고객의 상세한 아키텍처 설명
│    - 3가지 서비스의 오류 로그
│    - 관련 구성 파일
│
├─ 토큰 85,000개 -- 세션별 메모리
├─ 토큰 10,000개 -- 사용자의 현재 프롬프트
├─ 토큰 25,000개 -- 상세한 시스템 지침
│
v
┌─ 총 토큰 195,000개
│
v
┌─ LLM 컨텍스트 윈도우
│
├─ 검색됨
├─ 메모리
├─ 사용자
└─ 시스템
```

토큰 195,000개가 할당되고 5,000개가 응답 버퍼로 남습니다. 이 예시의 핵심은 **응답 용량을 지키면서 컨텍스트 활용을 극대화하는 균형**입니다. 이제 대화가 이어지며 오류 로그·스크린샷·문제 해결 시도가 추가되어 윈도우가 한계에 다다르면 세 가지 효과가 순차적으로 나타납니다.

1. **성능 저하**: 새 정보가 이전의 중요한 세부 정보를 밀어냅니다. 에이전트가 문제 이해에 필수인 "고객의 아키텍처 설명"을 사실상 망각합니다.
2. **우선순위 경합**: 원래 오류 로그와 새 문제 해결 시도 중 하나를 강제로 선택해야 하므로, 전체 컨텍스트를 못 써 응답 품질이 떨어집니다.
3. **계산 지연**: 모델이 더 큰 윈도우를 지원해도 컨텍스트가 커질수록 처리 오버헤드가 늘어 응답이 느려집니다.

> **💡 팁 — 반직관적 사실**: 컨텍스트 윈도우를 늘린다고 문제가 자동 해결되지 않습니다. **세심하게 큐레이팅한 5,000 토큰이, 포괄적이지만 산만한 50,000 토큰보다 성능이 좋은 경우가 많습니다.** 일부 모델은 컨텍스트가 길어질수록 오히려 정확도가 떨어집니다("Lost in the Middle"). "많이 넣기"가 아니라 "정확히 넣기"가 목표임을 강조하세요.

**토큰 경제학** — 컨텍스트 사용량은 토큰 소비를 거쳐 곧바로 운영 비용이 됩니다. 컨텍스트에 실린 데이터는 실제 참조 여부와 무관하게 매 요청 과금됩니다. 하루 10,000건을 처리하는 엔터프라이즈 애플리케이션에서 비효율적 컨텍스트 관리는 상당한 규모의 불필요한 비용을 누적시킵니다. 원칙은 하나입니다 — **모든 토큰은 의미 있는 가치를 제공해야 한다.**

> **💡 팁**: 현재 Amazon Bedrock 요금으로 실제 토큰 비용을 계산해 보이면 설득력이 큽니다. 최적화 전/후 컨텍스트 전략의 월간 비용 차이를 산출하는 연습을 넣으세요. (요금은 [Amazon Bedrock 요금 페이지](https://aws.amazon.com/bedrock/pricing) 참조)

#### 예산을 코드로 강제하기

위 배분표는 계획이고, 실제로 지켜지게 만드는 것은 코드입니다. 예산은 네 지점에서 강제됩니다.

```ascii
[토큰 예산을 강제하는 네 지점]

┌─ 1) 모델 호출 파라미터   maxTokens = 5,000
│    출력 토큰만 제한한다. 입력은 제한하지 않는다
│    TPM 쿼터는 요청 시작 시 (입력 + maxTokens) 로 선점된다
│
├─ 2) 시스템 프롬프트   예산을 문장으로 알린다
│    모델이 스스로 길이를 줄이게 만드는 소프트 제어
│
├─ 3) 핸드오프 계약   Pydantic 스키마로 입출력을 고정한다
│    전체 대화가 아니라 정해진 필드만 넘긴다
│
└─ 4) 루프 상한   limits={"total_tokens": ..., "turns": ...}
     에이전트 루프 전체의 누적 토큰을 막는다 (소프트 캡)

하드 상한은 1) 과 4), 소프트 유도는 2), 입력 크기 고정은 3) 이 담당한다
```

**1) `maxTokens` — 응답 버퍼를 상한으로 고정**

```python
from strands import Agent
from strands.models import BedrockModel

# 배분표를 그대로 상수로 옮긴다. 숫자를 코드 밖에 두면 계획과 구현이 어긋난다.
CONTEXT_WINDOW = 200_000
RESPONSE_BUDGET = 5_000                            # 응답 버퍼
INPUT_BUDGET = CONTEXT_WINDOW - RESPONSE_BUDGET    # 195,000

model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    # maxTokens 는 '출력' 토큰 상한이다. 입력을 제한하지 않는다.
    # 응답 버퍼와 같은 값으로 두면, 모델이 버퍼를 넘겨 생성하는 일을 구조적으로 막는다.
    max_tokens=RESPONSE_BUDGET,
    temperature=0.3,                               # 진단 업무이므로 낮게 둔다
)
```

> **⚠️ `maxTokens`를 넉넉하게 두면 안 되는 이유**: Bedrock은 요청 **시작 시점**에 `입력 토큰 + maxTokens`를 TPM/TPD 쿼터에서 선점하고, 응답이 끝난 뒤 실제 사용량으로 정산합니다. 요금은 실제 사용량만 청구되지만 **스로틀링은 선점 기준으로 걸립니다.** `maxTokens`를 32,000처럼 크게 두면 동시 처리량이 눈에 띄게 떨어집니다. 또한 출력 토큰에는 **번다운 배율**이 붙습니다(Claude 4.7 이하 5배, Sonnet 5·Opus 5 10배, 4.8 15배, 그 외 1:1). 출력은 입력보다 몇 배 비싼 자원입니다. ([토큰 계산 방식](https://docs.aws.amazon.com/bedrock/latest/userguide/quotas-token-burndown.html))

**2) 시스템 프롬프트에 예산을 명시**

```python
SYSTEM_PROMPT = f"""당신은 엔터프라이즈 기술 지원 에이전트입니다.

## 컨텍스트 예산 (준수 사항)
컨텍스트 윈도우는 {CONTEXT_WINDOW:,} 토큰이고 응답에 쓸 수 있는 예산은 {RESPONSE_BUDGET:,} 토큰입니다.

- 답변은 {RESPONSE_BUDGET:,} 토큰 안에서 끝냅니다. 초과분은 잘려 사용자에게 전달되지 않습니다.
- 오류 로그와 구성 파일을 그대로 되풀어 쓰지 않습니다. 판단 근거가 된 줄만 인용합니다.
- 이미 대화에 있는 내용을 요약해 반복하지 않습니다.
- 길어질 것 같으면 진단과 다음 조치만 먼저 제시하고, 세부는 요청받을 때 제공합니다.
"""
```

> **이것은 소프트 제어입니다.** 모델은 자기 출력 토큰을 정확히 세지 못하므로 이 지침이 예산을 보장하지는 않습니다. 하드 상한은 `maxTokens`가 담당하고, 프롬프트의 역할은 **잘리기 전에 스스로 줄이도록 유도**하는 것입니다. 둘은 대체 관계가 아니라 짝입니다. 덧붙여, 예산을 설명하는 이 문장들 자체가 시스템 예산(25,000 토큰)을 소비합니다.

**3) 핸드오프 계약 — 무엇을 넘기고 무엇을 넘기지 않는가**

핸드오프에서 예산이 가장 크게 새어 나갑니다. 전체 대화를 그대로 넘기면 수신 에이전트의 입력 토큰이 대화 길이에 비례해 늘어납니다. **스키마로 넘길 필드를 고정하면 입력 크기에 상한이 생깁니다.**

```python
from typing import Literal
from pydantic import BaseModel, Field


class DiagnosisHandoff(BaseModel):
    """기술 지원 에이전트 -> 청구 에이전트로 넘기는 페이로드.

    전체 대화가 아니라 아래 필드만 넘긴다. 필드와 길이를 고정했으므로
    수신 에이전트의 입력 토큰은 대화가 길어져도 늘어나지 않는다.
    """

    summary: str = Field(max_length=600, description="문제와 원인 요약. 로그 원문 금지")
    root_cause: Literal["config", "quota", "network", "bug", "unknown"]
    affected_services: list[str] = Field(max_length=5)
    evidence_lines: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="판단 근거가 된 로그 '줄'만. 로그 파일 전체 금지",
    )
    customer_tier: Literal["basic", "business", "enterprise"]
    next_action: str = Field(max_length=200, description="수신 에이전트가 바로 실행할 조치")


# 스키마만으로는 '무엇을 넣지 말 것인가'가 전달되지 않으므로 프롬프트로 보완한다.
HANDOFF_RULES = """
## 다른 에이전트로 넘길 때
- 전체 대화를 넘기지 않습니다. DiagnosisHandoff 스키마의 필드만 채웁니다.
- evidence_lines 에는 로그 '줄'만 최대 3개. 로그 파일이나 스택 트레이스 전체를 넣지 않습니다.
- 확실하지 않으면 추측하지 말고 root_cause 를 "unknown" 으로 둡니다.
- 수신 에이전트가 되묻지 않도록 next_action 을 반드시 채웁니다.
"""

support_agent = Agent(model=model, system_prompt=SYSTEM_PROMPT + HANDOFF_RULES)

result = support_agent(
    user_question,
    # 출력 형태를 스키마로 고정한다. 자유 텍스트를 파싱할 필요가 없어진다.
    structured_output_model=DiagnosisHandoff,
    # 4) 루프 전체의 누적 토큰·턴 상한. 상한에 닿으면 예외가 아니라
    #    턴 경계에서 정상 종료되고 stop_reason 에 이유가 담긴다.
    limits={"total_tokens": CONTEXT_WINDOW, "turns": 8},
)

handoff: DiagnosisHandoff = result.structured_output

# 수신 에이전트는 대화가 아니라 검증된 구조체만 받는다 → 입력 토큰이 예측 가능해진다
billing_reply = billing_agent(handoff.model_dump_json())
```

**예산 실측 — 계획대로 쓰였는지 확인**

```python
usage = result.metrics.latest_agent_invocation.usage

print(f"입력 {usage['inputTokens']:,} / 출력 {usage['outputTokens']:,} / 합계 {usage['totalTokens']:,}")
print(f"윈도우 대비 {usage['totalTokens'] / CONTEXT_WINDOW:.1%}")

# stop_reason 으로 '왜 끝났는지'를 구분해 대응을 나눈다
if result.stop_reason == "max_tokens":
    # 응답이 maxTokens 에서 잘렸다 → 응답 버퍼가 부족하거나 프롬프트 유도가 약하다
    print("응답 잘림: 응답 버퍼를 늘리거나 시스템 프롬프트에서 더 줄이게 유도할 것")
elif result.stop_reason in ("limit_total_tokens", "limit_output_tokens", "limit_turns"):
    # 루프 상한에서 멈췄다 → 예산 자체를 재검토하거나 컨텍스트를 줄일 것 (파트 2)
    print(f"루프 예산 상한에서 종료: {result.stop_reason}")
```

**주의할 점**

- **`maxTokens`는 입력을 막지 못합니다.** 입력 예산(195,000)은 별도로 관리해야 합니다 — 검색 결과 개수 제한, 대화 관리자, 압축이 그 수단이며 파트 2에서 다룹니다.
- **`limits`는 소프트 캡입니다.** 턴 경계에서만 검사하므로, 한 번의 큰 응답이 예산을 한 턴만큼 넘길 수 있습니다. 정확한 하드 상한이 필요하면 `maxTokens`를 함께 조여야 합니다.
- **`limits`는 호출 1회 단위입니다.** 같은 에이전트를 다시 호출하면 카운터가 초기화되며 누적되지 않습니다. 세션 전체 예산을 보려면 호출별 사용량을 애플리케이션이 합산해야 합니다.
- **동시에 여러 상한에 닿으면 우선순위가 있습니다** — `turns` > `total_tokens` > `output_tokens` 순으로 `stop_reason`이 정해집니다.
- `limits` 값에 양의 정수가 아닌 값을 주면 `TypeError`가 발생합니다.

### 1.5 모범 사례 (Well-Architected Agentic AI Lens)

- 🏛️ **AGENTPERF03-BP02 컨텍스트 윈도우 활용·프롬프트 관리**: 컨텍스트를 유한 리소스로 취급하고 구성 요소별로 예산을 배분한다. 200K 예산 배분 예시가 이 BP의 직접 실천이다.
- 🏛️ **AGENTCOST02 모델 호출·토큰 소비 비용 최적화 / AGENTCOST05 비용 귀속·추적**: 토큰이 곧 비용이므로, 범주별 토큰 사용을 추적·귀속해 낭비 지점을 식별한다.
- 🏛️ **AGENTSEC01-BP03 환각 전파 모니터링 / AGENTREL05-BP03 실제 정보에 인지를 근거**: 포이즈닝 실패 모드는 잘못된 컨텍스트가 잘못된 결론으로 전파되는 문제다. 검색·메모리 데이터의 신뢰성을 검증해 근거를 실제 정보에 고정한다.

---

## 파트 2. 컨텍스트 최적화 5대 전략 — 입력 형식·기록·선택·압축·분리

### 2.1 해결할 문제

파트 1에서 컨텍스트가 유한하고 비싸다는 것을 확인했습니다. 이제 문제는 **"어떻게 최적화할 것인가"** 입니다. 컨텍스트 최적화는 단일 기법이 아니라, 서로 보완하며 **동시에 적용 가능한 5가지 전략**으로 접근합니다. 특정 사용 사례의 요구와 성능 제약에 따라 이들을 조합합니다.

> 이 5대 전략 분류는 LangChain의 [컨텍스트 엔지니어링 정리](https://blog.langchain.com/context-engineering-for-agents)와 궤를 같이합니다.

### 2.2 고려해야 할 기술 — 5대 전략 개요

```ascii
┌─ 컨텍스트 최적화 5대 전략
│
├─ 1) 입력 형식 최적화 (토큰 인코딩 효율)
├─ 2) 기록(Write) (외부 스토리지 / 캐싱)
├─ 3) 선택(Select) (관련 컨텍스트만 어셈블)
├─ 4) 압축(Compress) (고충실도 요약)
├─ 5) 분리(Isolate) (전문가 에이전트 경계)
│
│  최적화된 컨텍스트 주입
v
┌─ LLM 컨텍스트 윈도우
└─ 유한 리소스
```

| 전략 | 핵심 아이디어 | 대표 구현 | 다루는 위치 |
| --- | --- | --- | --- |
| **① 입력 형식 최적화** | 동일 데이터를 더 적은 토큰으로 인코딩 | JSON→TOON/CSV, 스키마 단축, 프루닝 | 2.4-①(본문) |
| **② 기록(Write)** | 정보를 컨텍스트 밖 영구 스토리지로 외부화 | AgentCore Memory, 프롬프트 캐싱 | 2.4-②(메모리) + **파트 3(캐싱)** |
| **③ 선택(Select)** | 현재 목표에 가장 관련된 컨텍스트만 어셈블 | 시맨틱 검색(RetrieveMemoryRecords) | 2.4-③(본문) |
| **④ 압축(Compress)** | 의미를 보존하며 토큰 수를 축소 | SummarizingConversationManager | 2.4-④(본문) |
| **⑤ 분리(Isolate)** | 컨텍스트를 전문가 에이전트 경계로 분할 | 오케스트레이터-전문가 파이프라인 | 2.4-⑤(본문) |

> **💡 팁 — 순서가 아니라 계층**: 입력 형식 최적화는 **기초 전략**입니다. 데이터 파이프라인 초기에 토큰을 줄여 두면, 이후 기록·선택·압축·분리의 효과가 모두 증폭됩니다. 5개를 "택1"이 아니라 "겹쳐 쌓는 계층"으로 설명하세요.

### 2.3 구현 요건 및 절차 — 전략 선택

전략은 배타적이지 않지만, 워크로드의 지배적 특성에 따라 **1차 전략**을 고릅니다.

1. **세션 간 상태 지속이 핵심인가** → **기록(Write)**. 대화가 많고 며칠·몇 주에 걸쳐 재방문하며 이전 대화·주문·선호를 기억해야 하는 경우.
2. **지식 집약적이고 방대한 후보 중 골라야 하는가** → **선택(Select)**. 대규모 지식 기반에서 관련 조각만 뽑아야 하는 경우.
3. **한 세션이 매우 길어 컨텍스트가 계속 누적되는가** → **압축(Compress)**. 장기 실행 대화·연구 세션.
4. **여러 도메인이 얽혀 있는가** → **분리(Isolate)**. 복잡한 다중 도메인 애플리케이션.
5. **어느 경우든** → **입력 형식 최적화**를 기초로 항상 병행한다.

> **🧭 활동 — 전략 선택 시나리오**
> 대규모 전자상거래 플랫폼의 고객 지원 챗봇: 수천 개의 동시 대화, 고객이 며칠~몇 주에 걸쳐 재방문("지난주 배송 문의 기억하나요?"), 대화당 20~30회 교환, 이전 메시지를 자주 참조. **권장 전략은?**
>
> **정답: 기록(Write) 전략.** 세션 간 지속성이 필요한 상태 관리 중심의 대화 집약 애플리케이션이기 때문입니다. 정보를 영구 스토리지(AgentCore Memory·DynamoDB·RDS)로 외부화해 컨텍스트를 줄이면서, 여러 세션에서 고객 정보를 검색합니다. 세션 *내* 최적화만 하는 압축 전략보다, 세션 *간* 상태 지속이 핵심이라 기록이 우수합니다. (프로덕션에서는 기록 + 입력 형식 최적화 + 선택을 함께 씁니다.)
>
> **💡 팁**: 흔한 오해는 "대화가 기니까 압축"입니다. 세션 *간*(cross-session) 요구와 세션 *내*(in-session) 요구를 명확히 구분시키세요.

### 2.4 구현 예시 — 전략별 코드

#### ① 입력 형식 최적화 — TOON 예시

같은 정보라도 형식에 따라 토큰 비용이 다릅니다. JSON은 따옴표·대괄호·쉼표로 오버헤드가 크고, CSV는 테이블에 간결하며, YAML은 읽기 쉽지만 토큰이 많을 수 있습니다. **TOON(Token-Oriented Object Notation)** 은 세 형식의 장점을 결합한 오픈 소스 형식 최적화 *예시*입니다(규범적 권장이 아니라 하나의 기법).

```python
"""입력 형식 최적화 시연 — Pretty JSON vs TOON 실제 토큰 비교.
   Bedrock converse API를 호출해 모델이 실제로 센 inputTokens를 비교한다.
   실행: python M02-toon-token-comparison.py  (Contents/code/ 에 독립 스크립트 제공)
   사전 조건: AWS 자격 증명 + Bedrock 모델 접근 권한 + pip install boto3
"""
import json
import boto3

MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"  # 사용할 Bedrock 모델
client = boto3.client("bedrock-runtime", region_name="us-east-1")

# --- (A) Pretty JSON: 따옴표·중괄호·대괄호·쉼표 등 구문 오버헤드가 토큰을 늘린다 ---
data = {
    "context": {
        "task": "customer_support_session",
        "session_id": "sess_20250315_abc123",
        "timestamp": "2025-03-15T14:30:00Z",
    },
    "agents": ["billing_agent", "technical_agent", "shipping_agent"],
    "conversations": [{
        "id": 1, "role": "user",
        "content": "I need help with my order 45678",
        "agent": "billing_agent",
        "timestamp": "2025-03-15T14:31:00Z",
        "requiresResponse": True,
    }],
}
pretty_json_str = json.dumps(data, indent=2, ensure_ascii=False)

# --- (B) TOON: 계층 들여쓰기(YAML식) + 쉼표 구분 배열(CSV식) + 헤더 표기 객체 배열 ---
toon_str = """\
context:
  task: customer_support_session
  session_id: sess_20250315_abc123
  timestamp: "2025-03-15T14:30:00Z"
agents[3]: billing_agent,technical_agent,shipping_agent
conversations[1]{id,role,content,agent,timestamp,requiresResponse}:
  1,user,I need help with my order 45678,billing_agent,"2025-03-15T14:31:00Z",true"""

# --- Bedrock API로 실제 inputTokens 측정 ---
def measure(text: str) -> int:
    """텍스트를 user 메시지로 보내 모델이 실제로 센 inputTokens를 반환한다."""
    resp = client.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": text}]}],
        inferenceConfig={"maxTokens": 1},  # 응답 최소화(측정 목적)
    )
    return resp["usage"]["inputTokens"]

json_tok = measure(pretty_json_str)
toon_tok = measure(toon_str)
saved_pct = (1 - toon_tok / json_tok) * 100

print(f"Pretty JSON : {json_tok} 입력 토큰 | {len(pretty_json_str)} 문자")
print(f"TOON        : {toon_tok} 입력 토큰 | {len(toon_str)} 문자")
print(f"절감        : 토큰 {saved_pct:.1f}% ↓")
# 핵심: 동일 정보 · 형식만 변경 → 토큰 ~30% 절감. 반복 전송 시 누적 절감 극대화.
```

이 밖에도 입력 형식 최적화에는 **데이터 구조 최적화**(불필요 필드 제거·중첩 평면화·중복 제거), **스키마 설계**(짧은 필드 이름·메타데이터 최소화), **콘텐츠 프루닝**(태스크 무관 데이터 사전 제거)이 포함됩니다. TOON은 "형식 선택이 토큰 소비에 영향을 준다"는 원리를 보여주는 한 구현일 뿐이며, 테이블 데이터엔 CSV, 특수 사례엔 사용자 지정 형식이 더 나을 수 있습니다.

> **💡 팁**: TOON은 규범이 아니라 예시임을 반드시 명확히 하세요. 데모 도구([format-tokenization playground](https://www.curiouslychase.com/playground/format-tokenization-exploration))로 형식별 토큰 차이를 즉석에서 보여주면 효과적입니다. ([TOON 저장소](https://github.com/toon-format/toon))

#### ② 기록(Write) — AgentCore Memory로 외부화

기록 전략은 정보를 컨텍스트 윈도우 *밖* 영구 스토리지로 옮기되 접근성은 유지합니다. 대화 기록·사용자 선호·축적 지식을 활성 컨텍스트에 계속 담는 대신 외부에 저장합니다. **Amazon Bedrock AgentCore Memory**는 세션별(단기)·세션 간(장기) 지속성을 모두 제공하며, 대화 집약 애플리케이션에서 일반적으로 **40~60%의 컨텍스트 축소**를 달성합니다.

```python
# AgentCore Memory에 대화를 단기 메모리로 기록(외부화)한다.
# 장기 메모리는 단기 이벤트에서 '자동 추출'(비동기 백그라운드)되므로 직접 쓰지 않는다.
# 사전 조건: pip install boto3, AWS 자격 증명 구성, AgentCore Memory 리소스 생성 완료
import boto3
from datetime import datetime

client = boto3.client("bedrock-agentcore", region_name="us-east-1")

MEMORY_ID = "my-support-memory"        # AgentCore Memory 리소스 식별자
ACTOR_ID = "user-123"                  # 사용자별 식별자 → 다중 사용자 메모리 격리
SESSION_ID = "session-abc"             # 대화 세션 식별자

# 단기 메모리에 이벤트 기록 (CreateEvent)
# 매 상호작용을 이벤트로 적재한다. 이 원시 이벤트가 장기 메모리 추출의 원재료가 된다.
client.create_event(
    memoryId=MEMORY_ID,
    actorId=ACTOR_ID,
    sessionId=SESSION_ID,
    eventTimestamp=datetime.now(),
    payload=[
        {
            "conversational": {
                "content": {"text": "I prefer Python and email notifications."},
                "role": "USER",
            }
        }
    ],
)
# → 단기 메모리에 저장됨. 장기 메모리 전략이 설정돼 있으면
#   백그라운드에서 비동기로 요약·사실·선호가 자동 추출된다.
# 핵심: 정보를 컨텍스트 윈도우가 아닌 외부 스토리지에 기록(Write)했으므로
#       매 요청마다 토큰을 소비하지 않고, 나중에 필요할 때만 검색한다(→ ③ 선택 전략).
```

AgentCore Memory의 단기/장기 이중 구조와 시맨틱 검색(`RetrieveMemoryRecords`) 동작은 모듈 1의 메모리 아키텍처에서 상세히 다뤘습니다. 기록 전략의 또 다른 핵심 기법인 **프롬프트 캐싱**은 워낙 중요해 **파트 3**에서 별도로 심화합니다.

#### ③ 선택(Select) — 시맨틱 검색으로 관련 컨텍스트만

선택 전략은 "컨텍스트가 많은데 *무엇을* 넣을 것인가"에 답합니다. 사용 가능한 모든 컨텍스트를 로드하는 대신, **시맨틱 검색 + 우선순위 기반 선택**으로 현재 목표에 가장 관련된 레코드만 어셈블합니다. 응답 관련성이 **35~50% 향상**되면서 컨텍스트 팽창은 줄어듭니다.

```python
import boto3

client = boto3.client("bedrock-agentcore", region_name="us-east-1")

# 시맨틱 검색으로 현재 쿼리와 컨텍스트상 유사한 메모리 레코드를 검색
response = client.retrieve_memory_records(
    memoryId="conversation-history",                # AgentCore Memory 리소스 식별자
    namespace="/users/user-123/preferences",        # 필수: 계층적 네임스페이스(검색 범위 격리)
    searchCriteria={
        "searchQuery": "What are the user's preferences for data visualization?",  # 시맨틱 쿼리
    },
)

relevant_memories = response.get("memoryRecordSummaries", [])  # 결과 배열

# 관련성 점수로 후처리 필터링(API에 min_relevance_score가 없어 코드에서 수행)
selected_context = [
    memory["content"]["text"]                        # MemoryContent 객체의 text 필드 접근
    for memory in relevant_memories
    if memory.get("score", 0) > 0.8                  # 코사인 유사도 0.8 초과만 포함(높을수록 관련)
]

# 선택된 컨텍스트만 줄바꿈으로 이어 붙여 에이전트 프롬프트에 주입
agent_context = "\n".join(selected_context)
# 핵심: 전체 기록을 싣지 않고, 현재 상호작용에 필요한 과거 정보만 온디맨드로 로드한다.
```

> **💡 팁**: `topK`(반환 수)와 컨텍스트 윈도우 크기의 절충, 그리고 관련성 임계값(0.8) 설정이 곧 "컨텍스트 완전성 vs 토큰 효율" 조절 손잡이임을 강조하세요. `namespace`가 액터·세션·전략 단위로 메모리를 격리한다는 점도 함께.

#### ④ 압축(Compress) — 의미를 보존하며 토큰 축소

압축 전략은 **의미를 보존하며 토큰 수를 줄입니다.** 크게 두 가지 방식이 있습니다.
- **요약(Summarization)**: 오래된 메시지를 LLM으로 요약해 간결한 표현으로 대체.
- **트리밍(Trimming)**: 메시지 수 또는 토큰 수 기준으로 오래된 메시지를 제거.

두 방식 모두 프로덕션 에이전트 프레임워크에서 지원됩니다. 아래는 **LangGraph**와 **Strands** 의 압축 옵션 비교입니다.

**프레임워크별 압축 옵션 비교**

| 관점 | Strands Agents SDK | LangGraph |
| --- | --- | --- |
| **추상화** | 선언적 — 대화 관리자 클래스를 선택·파라미터 설정 | 명시적 — 그래프 노드·조건 분기로 직접 구현 |
| **트리밍** | `SlidingWindowConversationManager` (기본값, 고정 창) | `trim_messages` 유틸리티 또는 `RemoveMessage`로 상태에서 삭제 |
| **요약** | `SummarizingConversationManager` (자동 트리거·구조화 글머리 요약) | `summarize_conversation` 그래프 노드를 직접 작성 (조건부 실행) |
| **도구 페어 보존** | 내장 — 도구 호출-결과를 원자 단위로 보존 | 직접 로직 구현 필요 |
| **폴백 안전** | 내장 — 요약 실패 시 대화 계속 | 직접 에러 핸들링 구현 |
| **유연성** | 파라미터로 제어 (빠른 적용) | 노드 코드라 완전 자유 (커스텀 로직 가능) |
| **적합한 경우** | 빠른 프로토타이핑·표준 패턴 적용 | 복잡한 조건부 요약·커스텀 메모리 아키텍처 |

> **💡 팁**: 두 프레임워크의 압축 *전략*은 동일합니다(요약·트리밍). 차이는 *구현 방식*뿐입니다. Strands는 "설정"으로, LangGraph는 "코드"로 씁니다. LangGraph에서는 `summarize_conversation` 노드가 메시지 수 임계값을 초과하면 조건부로 실행되고, 요약을 `state["summary"]`에 저장한 뒤 원본 메시지를 `RemoveMessage`로 삭제합니다. 두 방식 다 결국 "오래된 메시지를 요약으로 대체"하는 같은 목적입니다.

**Strands 대화 관리자 3종**

| 대화 관리자 | 동작 | 적합한 경우 |
| --- | --- | --- |
| `NullConversationManager` | 대화 기록을 수정하지 않음 | 짧은 대화·디버깅(가장 투명) |
| `SlidingWindowConversationManager` | **기본값.** 고정 창 유지, 오래된 메시지 제거 | 최근 컨텍스트만 중요할 때 |
| `SummarizingConversationManager` | 오래된 메시지를 구조화 요약으로 압축 | 과거 컨텍스트가 중요한 장기 대화 |

`SummarizingConversationManager`는 토큰 제한 초과 시 오래된 메시지를 **삭제하지 않고 구조화된 글머리 기호 요약으로 압축**하며, 요약 중에도 **도구 사용-결과 메시지 페어를 원자 단위로 보존**해 대화 무결성을 지킵니다.

**Strands 구현 예시**

```python
from strands import Agent
from strands.models import BedrockModel
from strands.agent.conversation_manager import SummarizingConversationManager

# 사용할 모델 지정
model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0")

# 지능형 요약 기반 대화 관리자 구성
conversation_manager = SummarizingConversationManager(
    summary_ratio=0.3,              # 축소 시 요약할 메시지 비율(0.1~0.8로 자동 고정). 0.3=30% 압축
    preserve_recent_messages=10,    # 항상 원문 유지할 최근 메시지 최소 수 → 즉각적 대화 흐름 보존
    # summarization_agent=custom_agent,          # (선택) 요약 전용 커스텀 에이전트
    # summarization_system_prompt="도메인 용어 보존...",  # (선택) 요약용 커스텀 시스템 프롬프트
)

# 요약 대화 관리자를 적용한 에이전트 생성
# (conversation_manager를 지정하지 않으면 기본값인 SlidingWindowConversationManager가 사용됨)
agent = Agent(
    model=model,
    conversation_manager=conversation_manager,   # SummarizingConversationManager 적용
)
# 동작: 토큰 제한 초과 시 오래된 30%를 구조화 요약으로 압축하되,
#       최근 10개 메시지는 원문 보존, 도구 호출-결과 페어는 분리하지 않는다.
#       요약 실패 시에도 대화가 끊기지 않도록 폴백 안전 장치가 동작한다.
```

> **💡 팁 — 파라미터 감각**: `summary_ratio`가 너무 낮으면 압축 효과가 없고, 너무 높으면 정보 손실이 큽니다. 기본 0.3이 균형점입니다. `preserve_recent_messages`는 "최근 맥락은 절대 요약하지 않는다"는 안전선입니다. AgentCore Memory의 `AgentCoreMemorySessionManager`와 결합하면 *활성 컨텍스트는 압축*하고 *세션 간 정보는 지속*하는 완전한 수명 주기 관리가 됩니다.

#### ⑤ 분리(Isolate) — 전문가 에이전트 경계

분리 전략은 컨텍스트를 **여러 전문가 에이전트 경계로 분할**해, 각 에이전트가 자기 도메인 컨텍스트만 유지하게 합니다. 오케스트레이터는 최소 컨텍스트(라우팅·품질 가이드)만 갖고, 도메인 콘텐츠는 처리하지 않습니다. 개별 에이전트의 컨텍스트 요구를 **50~70% 낮출** 수 있습니다.

```ascii
┌─ 오케스트레이터 에이전트
│  최소 컨텍스트 / 태스크 라우팅 / 품질 가이드
│
├<--> 연구 에이전트
│       컨텍스트: 연구 논문
│
├<--> 분석 에이전트
│       컨텍스트: 데이터 및 통계
│
└<--> 보고서 에이전트
        컨텍스트: 연구 및 분석의 출력
```

핵심은 **각 에이전트가 자기 도메인 컨텍스트만 유지**한다는 것입니다. 오케스트레이터는 태스크 라우팅·품질 가이드만 들고 있고, 연구 에이전트는 논문만, 분석 에이전트는 데이터·통계만, 보고서 에이전트는 연구·분석의 출력만 봅니다. 에이전트 간 결과 전달은 오케스트레이터가 중재하며, 각자 전체 워크플로 컨텍스트를 공유하지 않으므로 개별 에이전트의 컨텍스트 부담이 50~70% 줄어듭니다.

```python
from strands import Agent, tool

# 전문가 에이전트를 @tool로 래핑하면 오케스트레이터가 호출 가능한 '도구'가 된다.
# (도구로서의 에이전트 패턴 — 모듈 1 참조). docstring이 라우팅 근거가 되므로 명확히 작성.
@tool
def research(query: str) -> str:
    """연구 논문·문헌을 검색해 인용과 핵심 결과를 '축약·종합'해 반환한다."""
    return str(research_agent(query))              # 내부적으로 연구 전문 에이전트 실행

@tool
def analyze(findings: str) -> str:
    """종합된 연구 결과에 정량 분석·통계를 적용한다(원본 논문은 받지 않음)."""
    return str(analysis_agent(findings))

@tool
def write_report(inputs: str) -> str:
    """연구 인사이트+분석 결과를 종합해 핵심 요약·권장이 담긴 보고서를 작성한다."""
    return str(report_agent(inputs))

# 오케스트레이터: 도메인 세부를 모른 채 '라우팅·종합'만 담당(최소 컨텍스트 유지)
orchestrator = Agent(
    model="anthropic.claude-opus-4-5",
    system_prompt=(
        "연구 워크플로를 조정한다. 문헌 조사는 research, 데이터 분석은 analyze, "
        "종합은 write_report로 위임하고 각 단계 품질을 보장한다."
    ),
    tools=[research, analyze, write_report],       # 전문가 에이전트(도구)들을 보유
)

# 상위 수준 태스크 한 줄 → 오케스트레이터가 위임 순서를 스스로 결정(모델 기반 위임)
result = orchestrator("재생 에너지 시장 분석 보고서를 작성하라")
```

> **💡 팁**: `@tool` 데코레이터가 왜 필요한지 자주 질문받습니다. 이 데코레이터는 함수의 docstring·타입 힌트에서 메타데이터를 추출해 LLM이 보는 **도구 스키마**를 자동 생성하고, 에이전트를 "호출 가능한 도구"로 변환합니다. 모델 기반 위임은 사전 정의된 워크플로 없이도 태스크에 따라 순차/병렬 실행을 유연하게 결정합니다.

### 2.5 모범 사례 (Well-Architected Agentic AI Lens)

- 🏛️ **AGENTCOST03-BP02 지능형 압축·컨텍스트 윈도우 프루닝**: 압축·선택 전략이 이 BP의 직접 실천이다. 요약·프루닝으로 정보 밀도를 유지하며 토큰을 줄인다.
- 🏛️ **AGENTSUS02-BP01 컨텍스트 관리·메모리 활용 최적화**: 지속 가능성 관점에서 컨텍스트·메모리 효율은 곧 리소스 효율이다.
- 🏛️ **AGENTCOST02-BP02 효율적 프롬프트 엔지니어링을 통한 토큰 소비 최적화**: 입력 형식 최적화(TOON·스키마 단축·프루닝)가 여기에 해당한다.
- 🏛️ **AGENTPERF03-BP01 계층형 메모리 / AGENTCOST03-BP01 계층형 메모리 기반 비용 효율 검색 / AGENTCOST03-BP03 상태 지속·수명 주기 관리**: 기록 전략(AgentCore Memory 단기·장기)의 근거. 세션 읽기(핫)와 장기 시맨틱 쿼리를 접근 패턴에 맞는 스토리지로 분리한다.
- 🏛️ **AGENTPERF05 오케스트레이션·협업 성능 / AGENTCOST01 추론·실행 비용 최적화**: 분리 전략의 근거. 전문가 경계로 에이전트당 컨텍스트를 낮춰 성능·비용을 함께 개선한다.

---

## 파트 3. 프롬프트 캐싱 — 정적 컨텍스트 재사용으로 지연·비용 절감

### 3.1 해결할 문제

기록 전략(파트 2-②)이 정보를 컨텍스트 *밖*으로 옮기는 것이라면, 프롬프트 캐싱은 **컨텍스트 안에 반드시 있어야 하지만 요청마다 동일한 부분**을 다루는 문제입니다. 시스템 프롬프트, 도구 정의, 참조 문서는 대화가 바뀌어도 거의 그대로입니다. 그런데 캐싱이 없으면 모델은 매 요청마다 이 정적 섹션을 **처음부터 다시 처리**하며 지연과 비용을 반복 지불합니다.

프롬프트 캐싱은 컨텍스트 윈도우를 **계층형 스토리지처럼** 취급해, 정적 섹션에 체크포인트를 표시하고 후속 요청에서 재처리를 생략합니다.

### 3.2 고려해야 할 기술

#### (1) Amazon Bedrock 프롬프트 캐싱

프롬프트 캐싱은 지원되는 모델에서 응답 지연을 줄이는 선택적 기능입니다. 정적 섹션에 캐시 체크포인트를 지정하면, **TTL(Time To Live)** 윈도우 내 후속 요청이 해당 섹션을 재처리하지 않고 캐시를 참조합니다. TTL은 모델에 따라 **5분 또는 1시간**을 선택할 수 있습니다(2026년 1월부터 1시간 옵션 추가).

```ascii
┌─ Amazon Bedrock (Claude / Nova 등 지원 모델)
│
├<-- 프롬프트 1 (캐시 체크포인트 지정)
│      1. 정적 섹션 캐시 기록 (CacheWriteInputTokens)
│
└<-- 후속 프롬프트 (TTL 5분 내 재사용)
       2. 캐시 참조 (CacheReadInputTokens / 저비용)
```

효과는 모델 응답의 두 필드로 **투명하게 측정**됩니다 — `CacheWriteInputTokens`(캐시에 새로 기록된 토큰)와 `CacheReadInputTokens`(캐시에서 읽은 토큰, 상당히 낮은 요금). 캐싱 사용 시 할인된 추론 요금이 적용되며, 캐시 읽기/쓰기 횟수에도 별도 요금이 붙습니다. ([Bedrock 프롬프트 캐싱 문서](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html))

#### (2) 정적 요소 우선(Static-First) 구조

캐싱을 살리려면 프롬프트를 **정적 → 동적 순서**로 구성해야 합니다. 모델은 프롬프트 접두사를 처음부터 일치시키므로, 앞쪽을 바꾸면 **그 뒤 모든 토큰의 캐시가 무효화**됩니다. 따라서 거의 변하지 않는 자산(시스템 지침·도구 정의·참조 문서)을 맨 앞에 두고, 매번 바뀌는 사용자 입력을 맨 뒤에 둡니다.

```ascii
┌─ 프롬프트 구조 (정적 요소 우선)
│
├─ 1) 시스템 지침 (정적 / 캐시됨)
│  v
├─ 2) 도구 정의 (정적 / 캐시됨)
│  v
├─ 3) 참조 문서 (정적 / 캐시됨)
│  v
├─ ===== 캐시 체크포인트 =====
│  v
└─ 4) 사용자 입력 (동적 / 매번 처리)
```

> **💡 팁**: 다중 에이전트 시스템에서 여러 에이전트가 동일한 시스템 지침·도구 정의를 쓰고, 그 텍스트가 모든 클라이언트에서 **동일하게 직렬화**되면 같은 캐시 항목을 공유해 전체 오버헤드를 더 줄일 수 있습니다. "정적 요소 우선"은 단일 에이전트뿐 아니라 다중 에이전트 캐시 공유의 전제입니다.

#### (3) 모델별 고려 사항 — Claude vs Nova

| 기능 | Anthropic Claude | Amazon Nova |
| --- | --- | --- |
| 모드 | Simplified(단일 포인트), Explicit(다중 포인트) | Automatic(지연↓), Explicit(비용↓+지연↓) |
| 비용 절감 | **두 모드 모두** | **Explicit 모드만** |
| 체크포인트 수 | 최대 4개 | 최대 4개 |
| 지원 TTL | 5분, 1시간 | 5분, 1시간 |
| 최소 토큰 | 1,024(대부분) · 2,048(Claude 3.5 Haiku) · 4,096(Opus 4.5·Haiku 4.5) | 1,000 |
| 지원 필드 | 시스템·메시지·도구 | 시스템·메시지 |

**핵심 차별점**: Nova의 **Automatic 모드는 지연 시간만** 줄이고 비용은 줄이지 않습니다. Nova에서 비용까지 절감하려면 **Explicit 모드 + 명시적 cachePoint 마커**를 써야 합니다. 반면 Claude는 두 모드 모두 비용을 절감합니다.

### 3.3 구현 요건 및 절차

1. **캐시 대상 식별**: 대화 간 거의 불변인 섹션을 찾는다 — 시스템 지침, 도구 정의, 대용량 참조 문서.
2. **최소 토큰 충족 확인**: 각 캐시 세그먼트가 모델의 최소 토큰(예: Claude Sonnet 4.5는 1,024)을 넘는지 확인한다. 미달이면 캐시되지 않는다.
3. **정적 요소 우선 배치**: 시스템 → 도구 → 참조 → (캐시 체크포인트) → 사용자 입력 순으로 구성한다.
4. **체크포인트 지정**: 정적 섹션 끝에 `cachePoint`를 둔다(최대 4개).
5. **지표 검증**: 1번째 요청 후 `cacheWriteInputTokens > 0`, 후속 요청에서 `cacheReadInputTokens > 0`을 확인한다.
6. **모델별 모드 선택**: 프로덕션 Nova는 Explicit 모드 권장(비용+지연 모두), Claude는 요구 정밀도에 따라 Simplified/Explicit 선택.

### 3.4 구현 예시 — Strands 캐싱 3종

Strands Agents SDK는 공급자 독립 인터페이스로 캐싱을 간소화하고, 지표를 `response.metrics.accumulated_usage`로 자동 노출합니다. ([Strands 캐싱 문서](https://strandsagents.com/docs/user-guide/concepts/model-providers/amazon-bedrock/#caching))

**(a) 시스템 지침 캐시** — 역할·어조·제약처럼 거의 안 변하는 부분.

```python
from strands import Agent
from strands.types.content import SystemContentBlock

# 정적 요소 우선: 시스템 지침(정적)을 먼저 캐시하고, 사용자 질문(동적)은 나중에 처리
system_content = [
    SystemContentBlock(
        text="""You are a professional customer service agent.
Role: Provide helpful, accurate responses
Tone: Friendly and professional
Constraints: Always verify information before responding"""
    ),
    SystemContentBlock(cachePoint={"type": "default"}),  # ← 캐시 끝 지점(명시적 체크포인트)
]

# 이 시스템 프롬프트로 에이전트 생성 → Strands가 캐싱 구성을 자동 처리
agent = Agent(system_prompt=system_content)
# 사용자 질문은 invoke로 직접 전달되어 캐시되지 않고 매번 동적으로 처리된다.
# 1번째 요청: cacheWriteInputTokens > 0(캐시 기록) / 후속 요청: cacheReadInputTokens > 0(저비용 재사용)
```

**(b) 도구 정의 캐시** — 도구를 추가/수정하지 않는 한 정적. `BedrockModel`에 한 줄만 추가.

```python
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator, current_time

bedrock_model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
    cache_tools="default",          # ← 도구 정의 캐싱 활성화(한 줄). 모든 도구가 한 단위로 캐시됨
)

agent = Agent(
    model=bedrock_model,
    tools=[calculator, current_time],  # 이 도구 정의들이 함께 캐시된다
)
# 사용자 요청은 동적 처리. 동일 도구 구성을 반복 사용하는 프로덕션에서 캐시 재사용으로 비용 절감.
```

**(c) 참조 문서 캐시** — 회사 정책·제품 사양 등 대용량 정적 콘텐츠. 문서 하나를 캐시해 여러 질문에 답한다.

```python
# 메시지 콘텐츠 배열에 문서 블록 → 지침 텍스트 → cachePoint 순으로 배치(정적 요소 우선)
messages = [
    {
        "role": "user",
        "content": [
            {
                "document": {
                    "format": "txt",
                    "name": "knowledge_base",
                    "source": {"bytes": b"Company Policies document, 2000+ tokens"},
                }
            },
            {"text": "Use this document to answer questions."},  # (선택) 지침 텍스트
            {"cachePoint": {"type": "default"}},                 # ← 여기까지 캐시(문서+지침)
        ],
    }
]
# 대용량 문서(토큰 1,000개 이상)는 최소 토큰 임계값을 자동 충족한다.
# 1번째 요청: 문서 캐시 기록 / 동일 문서 후속 요청: 캐시에서 저비용 읽기.
# 문서 Q&A처럼 같은 문서에 질문만 바뀌는 경우 비용을 크게 절감(사례: 최대 86% 절감).
```

> **💡 팁 — API 형태 구분**: 세 예시는 캐싱 지정 위치가 다릅니다. **시스템**은 `SystemContentBlock` 배열, **도구**는 `BedrockModel(cache_tools=...)` 구성, **문서**는 메시지 콘텐츠의 `cachePoint`. "무엇을 캐시하느냐"에 따라 지정 방식이 달라진다는 점을 표로 대조해 주세요.

### 3.5 모범 사례 (Well-Architected Agentic AI Lens)

- 🏛️ **AGENTPERF03-BP04 에이전트 캐싱·데이터 액세스 패턴**: 프롬프트 캐싱은 정적 섹션 재처리를 생략해 지연을 줄이는 대표적 캐싱 패턴이다. 정적 요소 우선 구조가 캐시 적중률을 좌우한다.
- 🏛️ **AGENTCOST02-BP03 지능형 캐싱으로 중복 모델 호출 감소**: 반복되는 시스템·도구·문서 토큰을 캐시 재사용으로 대체해 입력 토큰 비용을 직접 절감한다. `CacheReadInputTokens`로 절감 효과를 측정·귀속한다.
- 🏛️ **AGENTPERF02 응답 지연 최적화(참고)**: 캐싱은 첫 토큰까지 시간(TTFT)을 낮추는 수단 중 하나다. 스트리밍 등 다른 지연 최적화와 병행하면 체감 성능이 개선된다.

---

## 파트 4. 컨텍스트 효율성을 위한 도구 설계

### 4.1 해결할 문제

에이전틱 시스템의 **모든 도구 호출은 컨텍스트 윈도우 토큰을 소비**합니다. 도구 계층은 세 가지 벡터로 컨텍스트를 잠식합니다. (아래 백분율은 특정 논문 수치가 아니라 프로덕션에서 흔히 관찰되는 대표적 패턴입니다.)

| 소비 벡터 | 비중(예시) | 내용 |
| --- | --- | --- |
| **도구 응답** | ~40% | API·DB·파일에서 반환된 실제 데이터 페이로드 |
| **중복 데이터** | ~35% | 도구 기능 중복으로 유사 정보를 여러 형식·여러 호출로 수집 |
| **오류 메시지** | ~25% | 스택 추적·검증 오류·디버깅 정보 |

가장 은밀한 낭비는 **중복 데이터**입니다. 예를 들어 고객 데이터를 위해 기본 프로필·구매 내역·선호·연락처·로열티를 각각 다른 도구로 5번 호출하면, 통합 도구 하나보다 훨씬 많은 컨텍스트를 씁니다. 목표는 **소비한 토큰당 정보 가치를 극대화**하는 것입니다.

### 4.2 고려해야 할 기술 — 3가지 접근

1. **정보 집약형 도구 아키텍처**: 여러 소규모 호출을 하나의 포괄적 호출로 통합.
2. **MCP 서버 중앙 집중화**: 여러 에이전트가 공유하는 도구를 중앙 서버로 모아 중복 제거.
3. **집중형 도구 세트 설계**: 단일 책임 원칙으로 도구 경계를 명확히 해 혼동·시행착오 감소.

### 4.3 구현 요건 및 절차

**A. 정보 집약형 도구 — 응답 구현 3원칙**
1. **계층적 JSON**: 논리적 그룹화 + 데이터 관계·신선도 메타데이터로 구조화해 에이전트가 효율적으로 파싱하게 한다.
2. **스마트 오류 처리**: 긴 스택 추적 대신 구조화된 `null` 응답으로 데이터 가용성만 전달한다.
3. **컨텍스트 인식 필터링**: 현재 태스크와 가장 관련된 섹션만 우선 반환한다.

**B. MCP 중앙 집중화 — 구현 고려**
1. 서버에서 도구를 **범주화**하고, AWS IAM으로 적절히 **인증**한다.
2. 여러 에이전트가 의존하므로 **고가용 설계 + 로드 밸런싱**을 적용한다.
3. AgentCore Gateway로 노출하면 `도구 나열·호출·검색`이 표준화된다(모듈 1의 Gateway 절차 참조).

**C. 집중형 도구 세트 — 단일 책임**
1. **기능 감사**로 중복·격차를 식별한다.
2. 각 도구에 **명확한 경계**를 정의한다(예: 결제 도구는 결제만, 고객 조회는 하지 않음).
3. 한 도구 변경이 다른 도구에 영향을 주지 않게 해 **테스트·최적화·유지 관리**를 쉽게 한다.

### 4.4 구현 예시

#### (1) 정보 집약형 JSON 응답

3회 개별 호출(`getBasicCustomerInfo` + `getCustomerPreferences` + `getCustomerHistory`)을 **단일 `getCompleteCustomerProfile()`** 로 통합하고, 응답에 3원칙을 모두 담습니다.

```python
def get_complete_customer_profile(customer_id: str, context_filter: str) -> dict:
    """3회 개별 호출을 대체하는 통합 도구. 계층적 JSON·스마트 오류·컨텍스트 필터링 적용."""
    return {
        # ① 계층적 JSON: 메타데이터로 데이터 관계·신선도·필터를 설명
        "metadata": {
            "data_freshness": "2024-10-26T10:00:00Z",  # 신선도 → 에이전트가 최신성 판단
            "source_system": "CRM-Prod",
            "context_filter": context_filter,          # ③ 컨텍스트 인식 필터링 신호
        },
        "basic_info": {                                 # 논리적 그룹화
            "customer_id": customer_id, "name": "Jane Doe",
            "status": "Active", "email": "jane.doe@example.com",
        },
        "preferences": {
            "communication_channel": "email", "language": "en-US",
        },
        "interaction_history": [
            {"date": "2024-10-25", "type": "Support Ticket",
             "summary": "Resolved billing inquiry", "status": "closed"},
        ],
        "account_details": {
            "plan_type": "Enterprise",
            # ② 스마트 오류 처리: 데이터 없음을 긴 오류 대신 구조화 null로 전달(토큰 절약)
            "billing_history": None,
        },
    }
# 결과: 개별 호출 3회 → 통합 호출 1회. 요청·응답 컨텍스트 사용 감소 + 성능 향상.
```

> **💡 팁**: `billing_history: null`은 "데이터 없음"을 장황한 오류 없이 알리는 패턴입니다. `context_filter` 메타데이터는 현재 태스크에 맞춰 어느 섹션이 중요한지 표시해 우선순위를 정하게 합니다. 통합 도구의 응답 설계가 곧 토큰 효율임을 강조하세요.

#### (2) MCP 서버 중앙 집중화

여러 에이전트가 같은 도구를 각자 구현하면 중복이 발생합니다. 도구를 **MCP 서버**로 모으면 중복 구현이 사라지고, 응답 형식이 일관되며, 공유 캐싱이 가능해집니다.

```ascii
[이전 (도구 중복)]

┌─ 에이전트 A
├─ 에이전트 B
│
├──> 도구
└──> 도구
       연결 4개 (에이전트 2 x 도구 2)

[이후 (MCP 서버 중앙 집중화)]

┌─ 에이전트 A
├─ 에이전트 B
│
└──> MCP 서버
       도구 1..n / 단일 정의
       연결 2개 (에이전트 2 x MCP 서버 1)
```

**AgentCore Gateway** 로 MCP 서버를 노출하면 인증·라우팅·프로토콜 변환이 투명하게 처리됩니다. 에이전트는 백엔드가 Lambda든 REST API든 다른 MCP 서버든 **동일한 MCP 인터페이스**로만 상호작용하며, 백엔드를 바꿔도 에이전트 코드는 그대로입니다.

```ascii
┌─ 에이전트 (MCP 클라이언트)
│
│  streamable HTTP
v
┌─ AgentCore Gateway (도구 나열 / 호출 / 검색)
│
├─ 토큰 검증
│  v
│  ┌─ AgentCore Identity
│  │
│  └─ 인바운드 인증
│     v
│     └─ 자격 증명 공급자 (Cognito / Okta / Auth0)
│
└─ 아웃바운드 인증 (OAuth / IAM)
   v
   └─ MCP 서버 (도구 1..n)
```

#### (3) 시맨틱 도구 검색 — 컨텍스트 인식 필터링

수백 개의 도구가 있으면 **도구 정의만으로도** 컨텍스트가 잠식됩니다. AgentCore Gateway의 시맨틱 검색을 켜면, Gateway가 모든 도구의 벡터 임베딩을 사전 계산해 두고, 에이전트가 자연어 쿼리로 **상위 10개 관련 도구만** 받습니다(전체 300개+ 대신).

```ascii
[검색 미사용]

┌─ AgentCore Gateway
│
├──> 대상 1 (175 도구)
├──> 대상 2 (150 도구)
├──> 대상 3 (10 도구)
│
└──> 300+ 도구 전체 반환 (컨텍스트 과소비)

[검색 사용 (시맨틱)]

┌─ '고객 지원 티켓 생성'
│
│  자연어 쿼리
v
┌─ AgentCore Gateway
│
└──> 상위 10개 관련 도구만 반환
```

에이전트는 검색이 켜지면 도구 목록의 맨 앞에 나타나는 `x_amz_bedrock_agentcore_search` 도구로 "고객 지원 티켓 생성" 같은 쿼리를 던져, 의도에 맞는 소수 도구만 받습니다. 도구 정의에 쓰는 토큰이 줄어 실제 실행·응답 처리에 더 많은 컨텍스트를 쓸 수 있습니다.

> **💡 팁 — 생성 시 결정**: 시맨틱 검색은 **Gateway 생성 중에만 활성화**할 수 있고 생성 후에는 켤 수 없습니다. 대규모 도구 카탈로그를 설계할 때 반드시 미리 계획하도록 강조하세요.

### 4.5 모범 사례 (Well-Architected Agentic AI Lens)

- 🏛️ **AGENTCOST02 토큰 소비 비용 최적화**: 정보 집약형 도구가 여러 호출을 하나로 합쳐 요청·응답 토큰을 직접 줄인다.
- 🏛️ **AGENTOPS04-BP02 표준 통합 프로토콜(MCP·A2A) / AGENTPERF04 효율적 프로토콜 통신**: MCP 중앙 집중화와 Gateway 표준화가 중복을 제거하고 프로토콜 효율을 높인다.
- 🏛️ **AGENTPERF03-BP02 컨텍스트 인식 필터링**: 시맨틱 도구 검색이 현재 태스크 관련 도구만 노출해 컨텍스트 소비를 줄인다. (대규모 카탈로그에서 특히 효과적)
- 🏛️ **AGENTREL02-BP01 원자적·집중형 설계**: 단일 책임 도구 세트는 에이전트의 도구 선택 정확도를 높이고 시행착오 컨텍스트 낭비를 줄인다.

---

## 파트 5. 프로덕션 구현 종합 체크리스트

파트 1~4의 전략을 프로덕션에 올릴 때 점검합니다.

- **토큰 예산 명시**: 모델 윈도우에서 응답 버퍼를 먼저 예약하고 5범주에 예산을 배분한다. 범주별 토큰 사용을 계측한다. (파트 1)
- **전략 조합**: 워크로드 특성에 맞는 1차 전략을 고르되, 입력 형식 최적화는 항상 병행한다. 세션 간 지속=기록, 지식 집약=선택, 장기 대화=압축, 다중 도메인=분리. (파트 2)
- **캐시 계측**: 정적 요소 우선 구조로 배치하고 `CacheWriteInputTokens`/`CacheReadInputTokens`로 적중률·절감을 검증한다. Nova 프로덕션은 Explicit 모드. (파트 3)
- **도구 계층 정리**: 정보 집약형 통합 도구 + MCP 중앙 집중화 + 대규모 카탈로그는 시맨틱 검색(생성 시 활성화). (파트 4)
- **컨텍스트 품질 모니터링**: 4대 실패 모드(포이즈닝·주의 분산·혼동·충돌)의 조기 징후를 관찰·계측한다. (→ 모듈 4 관찰성)
- **비용 귀속**: 컨텍스트 사용량을 비용으로 환산해 추적하고, 최적화 전/후를 정량 비교한다.
- **간단하게 시작 → 반복**: 최소 컨텍스트로 시작해 근거를 확인하며 전략을 더한다.

---

## Well-Architected Agentic AI Lens 매핑 (요약 레퍼런스)

> 기준: [AWS Well-Architected Agentic AI Lens](https://docs.aws.amazon.com/ko_kr/wellarchitected/latest/agentic-ai-lens/agentic-ai-lens.html) (2026-06-10 발행, 6개 기둥·41개 질문·150개 BP). 본문 각 파트의 🏛️ 표시가 해당 모범 사례이며, 아래는 매핑·보완 요약입니다.

| 본 모듈 주제 | 관련 모범 사례(BP) |
| --- | --- |
| 유한 리소스·토큰 예산·컨텍스트 윈도우 (파트 1) | AGENTPERF03-BP02, AGENTCOST02, AGENTCOST05 |
| 컨텍스트 실패 모드(포이즈닝 등) (파트 1) | AGENTSEC01-BP03, AGENTREL05-BP03 |
| 입력 형식 최적화 (파트 2-①) | AGENTCOST02-BP02 |
| 기록·외부 스토리지·AgentCore Memory (파트 2-②) | AGENTPERF03-BP01, AGENTCOST03-BP01, AGENTCOST03-BP03 |
| 선택·시맨틱 검색 (파트 2-③) | AGENTCOST03-BP02, AGENTPERF03-BP02 |
| 압축·요약 (파트 2-④) | AGENTCOST03-BP02, AGENTSUS02-BP01 |
| 분리·전문가 에이전트 (파트 2-⑤) | AGENTPERF05, AGENTCOST01 |
| 프롬프트 캐싱 (파트 3) | AGENTPERF03-BP04, AGENTCOST02-BP03 |
| 도구 설계·MCP 중앙 집중·시맨틱 도구 검색 (파트 4) | AGENTCOST02, AGENTOPS04-BP02, AGENTPERF04, AGENTREL02-BP01 |
