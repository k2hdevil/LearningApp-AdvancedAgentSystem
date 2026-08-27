# 모듈 1 · 다중 에이전트 아키텍처 및 통신 패턴 (심화 학습 가이드)

> Building Advanced Agentic Systems on AWS (한국어) · 300레벨 심화
> 원본 강사 덱: `MLADAS-10-KO-KR-M01-MultiAgent_InstructorDeck.pptx` (총 46개 슬라이드)
> 슬라이드 전사본을 아래 4가지 관점으로 재구성했습니다. 원본 슬라이드 전사본은 `_slide-transcript-backup/`에 보관되어 있습니다.
>
> **① 문제 해결에 고려할 기술·서비스·기능 → ② 구현 요건·절차 → ③ 구현 예시 → ④ 모범 사례(Well-Architected Agentic AI Lens 통합)**

---

## 학습 목표 및 선수 지식

**이 모듈을 마치면 다음을 수행할 수 있습니다.**
- 단일 에이전트의 한계를 진단하고 다중 에이전트 전환이 정당한 시나리오를 판별한다.
- 3가지 통신 패턴(프레임워크 계층 · 도구로서의 에이전트 · A2A)과 3가지 오케스트레이션(워크플로 · 그래프 · 스웜)을 선택·구현한다.
- AgentCore Memory와 Strands 상태 공유로 다중 에이전트 메모리를 설계·구현한다.
- 각 결정을 Well-Architected Agentic AI Lens 모범 사례에 근거해 검증한다.

**선수 지식**: AgentCore 기본(Runtime/Memory/Gateway), Strands Agents SDK 기초, 분산 시스템·마이크로서비스 개념, AWS IAM/네트워킹 기초.

---

## 모듈 개요 — 이 모듈이 푸는 3가지 문제

다중 에이전트 시스템 설계는 결국 세 가지 질문에 답하는 과정입니다.

| 파트 | 핵심 질문 | 산출물 |
| --- | --- | --- |
| 1. 아키텍처 결정 | *언제·왜* 다중 에이전트로 나누는가? | 에이전트 경계와 책임 정의 |
| 2. 통신·오케스트레이션 | 나눈 에이전트를 *어떻게* 연결·조정하는가? | 통신 패턴 + 오케스트레이션 선택 |
| 3. 메모리·상태 | 에이전트 간 컨텍스트를 *무엇으로* 유지하는가? | 공유 메모리·상태 아키텍처 |

> **Well-Architected 설계 원칙(전제)**: Agentic AI Lens의 첫 번째 설계 원칙은 *"에이전트 워크로드를 전문화·경계가 명확한 에이전트로 분해하라"* 입니다. 이 원칙이 나머지 모든 기둥(보안·신뢰성·성능·비용)의 제어를 가능하게 하는 토대입니다. 이 모듈 전체가 이 원칙의 구체적 실천입니다.

---

## 파트 1. 언제·왜 다중 에이전트로 전환하는가 (아키텍처 의사결정)

### 1.1 해결할 문제

단일 에이전트는 세 가지 구조적 한계에 부딪히며, 이것이 다중 에이전트의 근본 동인입니다.

- **인지 부하 한계(Cognitive load)**: 하나의 에이전트가 기술·제품·청구처럼 이질적 도메인을 동시에 처리하면, 지식 기반·용어·문제 해결 방식을 계속 전환하며 계산 오버헤드가 발생하고, 한 도메인의 로직을 다른 도메인에 잘못 적용해 오류가 연쇄됩니다.
- **컨텍스트 윈도우 고갈(Context exhaustion)**: 대화 기록·도구 출력·문서·추론 단계가 누적되면 토큰 한계에 도달합니다. 어텐션 연산은 시퀀스 길이에 따라 비용이 제곱으로 증가하므로, 윈도우를 키우는 것만으로는 해결되지 않고 오히려 "Lost in the Middle"(중간 정보 소실)과 지연이 심해집니다.
- **도메인 전문화 절충(Specialization vs. generalization)**: 일반 에이전트는 깊이가 부족하고, 과도하게 전문화된 에이전트는 엣지 케이스·다중 도메인 요청에 취약합니다.

> **💡 심화 보충 — 컨텍스트 윈도우는 실제로 어떻게 동작하는가 (제곱 비용 · 기억 · 다중 에이전트)**
>
> **① 왜 "제곱(quadratic)"인가.** 트랜스포머의 self-attention(자기 어텐션)은 **모든 토큰이 다른 모든 토큰과 관련도(attention score)를 계산**합니다. 토큰 수가 N이면 N×N개의 쌍을 계산하므로(내부적으로 N×N 어텐션 행렬 생성), 입력 길이를 2배로 늘리면 연산은 2배가 아니라 **4배(2²)** 가 됩니다 → O(N²), 제곱 복잡도.
>
> ```ascii
> [제곱 비용]  self-attention 은 모든 토큰 쌍의 관련도를 계산한다
>
> 토큰 4개  =>  4 x 4 = 16 쌍
>      t1 t2 t3 t4
>   t1  x  x  x  x
>   t2  x  x  x  x
>   t3  x  x  x  x
>   t4  x  x  x  x
>
> 토큰 8개  =>  8 x 8 = 64 쌍   (길이는 2배인데 계산은 4배)
>      t1 t2 t3 t4 t5 t6 t7 t8
>   t1  x  x  x  x  x  x  x  x
>   t2  x  x  x  x  x  x  x  x
>   t3  x  x  x  x  x  x  x  x
>   t4  x  x  x  x  x  x  x  x
>   t5  x  x  x  x  x  x  x  x
>   t6  x  x  x  x  x  x  x  x
>   t7  x  x  x  x  x  x  x  x
>   t8  x  x  x  x  x  x  x  x
>
> 행과 열이 각각 2배가 되므로 칸은 4배  =>  O(N^2)
> ```
>
> - 1,000 토큰 → 약 100만 연산 (기준)
> - 2,000 토큰 → 약 400만 (길이 2배인데 **연산 4배**)
> - 10,000 토큰 → 약 1억 (길이 10배인데 **연산 100배**)
>
> 연산량뿐 아니라 **지연 시간·메모리**도 같은 비율로 급증합니다.
>
> **② 컨텍스트 윈도우 = "저장소"가 아니라 매 호출 입력 전체.** 컨텍스트 윈도우는 토큰이 쌓이는 메모리가 아니라 **1회 처리 최대 용량(한계)** 입니다. 위 N은 그 호출에 들어가는 입력 전체이며, 여기에는 **시스템 프롬프트 + 대화 기록 + 검색 문서(RAG) + 도구 정의 + 도구 출력 + 현재 메시지(+ 생성 중 출력)** 가 모두 포함됩니다. 즉 "프롬프트 토큰"과 "윈도우에 저장된 토큰"은 별개가 아니라 같은 것입니다.
>
> ```ascii
> [윈도우의 정체]  저장소가 아니라 '1회 호출 입력 전체'
>
> 매 호출마다 아래가 전부 합쳐져 N 이 된다
>
> ┌─ 1회 호출에 들어가는 입력 (= N 토큰)
> │
> ├─ 시스템 프롬프트
> ├─ 대화 기록 (지금까지의 모든 턴)
> ├─ 검색 문서 (RAG)
> ├─ 도구 정의
> ├─ 도구 출력
> ├─ 현재 사용자 메시지
> └─ 생성 중인 출력
>
> 컨텍스트 윈도우 = 이 합계의 상한 (1회 처리 최대 용량)
> ```
>
> **③ 그럼 이전 대화는 어떻게 "기억"되나.** LLM은 **상태가 없습니다(stateless)** — 호출 사이에 아무것도 저장하지 않습니다. 애플리케이션이 대화 기록(`messages` 배열: system/user/assistant/tool)을 보관했다가 **매 호출마다 전체를 다시 입력에 넣어** 보냅니다. 그래서 대화가 길어질수록 매 턴 N이 커지고, 같은 기록에 대한 입력 토큰을 반복 지불합니다. (훈련으로 학습한 **가중치 기억**과, 이렇게 입력에 넣는 **인컨텍스트 기억**은 다릅니다. 대화는 후자입니다.)
>
> ```ascii
> [stateless]  LLM 은 호출 사이에 아무것도 저장하지 않는다
> 기억은 모델이 저장하는 것이 아니라 애플리케이션이 매번 다시 넣어주는 것
>
> 턴 1
>   앱이 보내는 입력: [SYS][U1]                    N = 2
>   모델 응답: A1
>
> 턴 2
>   앱이 보내는 입력: [SYS][U1][A1][U2]            N = 4
>   모델 응답: A2
>
> 턴 3
>   앱이 보내는 입력: [SYS][U1][A1][U2][A2][U3]    N = 6
>   모델 응답: A3
>
> 모델은 직전 응답조차 기억하지 않는다
> 같은 [SYS][U1][A1] 을 매 턴 다시 보내고, 매 턴 다시 과금된다
> ```
>
> **④ 그래서 다중 에이전트가 절약하는 것.** 핵심은 모델 크기가 아니라 **컨텍스트 분산**입니다. 크기 N의 컨텍스트를 k개 에이전트(각 ~N/k)로 나누면 어텐션 비용이 ~N² → **~N²/k** 로 줄고, 각 창이 작아 "Lost in the Middle"(중간 정보 소실)도 완화됩니다. 단, 오케스트레이션·요약 전달 등 **조정 오버헤드**가 있어 시스템 전체 토큰 총량이 주는 것은 아닙니다. AgentCore Memory는 전체 기록을 매번 넣는 대신 **관련 부분만 검색해 주입**해 N을 줄입니다(→ 모듈 2).
>
> ```ascii
> [컨텍스트 분산]  다중 에이전트가 실제로 절약하는 것
>
> 단일 에이전트  N = 12 를 하나가 다 들고 간다
>   어텐션 비용   12 x 12 = 144
>
> k = 3 으로 나누면  각 에이전트는 N/k = 4
>
>   에이전트 A      4 x 4 = 16
>   에이전트 B      4 x 4 = 16
>   에이전트 C      4 x 4 = 16
>   합계                    48
>
> 144  ->  48   (N^2  ->  N^2/k, 즉 1/3)
> 각 창이 작아지므로 중간 정보 소실(Lost in the Middle)도 완화된다
>
> 단, 시스템 전체 토큰 총량이 주는 것은 아니다
>   오케스트레이션과 요약 전달에 조정 오버헤드가 추가된다
> ```
>
> **완화 기법**: FlashAttention(메모리 효율화) · KV 캐시(생성 시 재계산 방지) · 희소/슬라이딩 윈도우 어텐션. 다만 "길수록 비싸다"는 기본 방향은 동일합니다.

### 1.2 고려해야 할 기술·서비스·기능

다중 에이전트로 분해하면 마이크로서비스와 동일한 이점을 얻습니다 — **구성 요소 재사용성 · 격리 · 유지 관리성 · 확장성 · 내결함성 · 복원력**. 핵심 기술 요소는 다음과 같습니다.

| 요소 | 역할 | AWS/오픈소스 |
| --- | --- | --- |
| 에이전트 런타임 | 각 전문 에이전트를 독립 배포·격리·스케일 | **Amazon Bedrock AgentCore Runtime** (서버리스, 대화별 마이크로 VM 격리, 자동 스케일) |
| 에이전트 프레임워크 | 에이전트 로직·오케스트레이션 구현 | **Strands Agents SDK**, LangGraph, CrewAI |
| 기반 모델 | 추론 엔진 | Amazon Bedrock (Nova, Claude 등) |

**전문화의 형태**도 함께 고려합니다. 분해 축은 두 가지입니다 — *무엇(주제)* 으로 나누는 **도메인 전문화**(주문·청구 등)와, *어떤 사고 방식* 으로 나누는 **인지 기능 전문화**(cognitive/functional specialization: 창의·논리 추론·검색/기억 전담)입니다. 두 축은 직교하므로 함께 적용할 수 있습니다(예: 법률 도메인 내에서도 검색·추론·작성 에이전트로 분리).

**다이어그램: 단일 에이전트의 절충 vs 다중 에이전트 분해**

```ascii
[단일 에이전트]  기술 + 청구 + 제품을 하나가 모두 담당

     심층적 전문성  <-->  광범위한 지원 범위
     둘 중 하나를 포기해야 하는 절충 관계
     깊게 파면 범위가 좁아지고, 범위를 넓히면 얕아진다

  │
  │  인지 기능 전문화로 분해
  v

[다중 에이전트]  분해해서 두 장점을 동시에 확보

┌─ 오케스트레이터
│  라우팅과 결과 종합만 담당 (도메인 작업은 직접 하지 않는다)
│
├──> 고객 서비스 에이전트  (주문 / 배송 문의)
├──> 제품 반품 에이전트  (반품 / 환불 처리)
└──> 제품 정보 에이전트  (추천 / 사양 안내)

     에이전트 하나하나는 깊게, 시스템 전체로는 넓게
```

### 1.3 구현 요건 및 절차 — 다중 에이전트 채택 결정

다중 에이전트는 조정 오버헤드·비용·복잡성을 수반하므로, **분해는 근거가 있을 때만** 수행합니다. 다음 절차를 따릅니다.

1. **한계 진단**: 현재(또는 예상) 워크로드가 인지 부하·컨텍스트 고갈·전문화 절충 중 무엇에 부딪히는지 식별한다.
2. **결정 기준 평가**: 아래 5개 기준 중 해당 항목이 많을수록 다중 에이전트가 유리하다.
   - 여러 도메인에 걸친 **심층 전문성**이 필요한가?
   - 정교한 **조정(orchestration)** 이 필요한가?
   - 팀 간 **재사용** 기회가 있는가?
   - 기능별 **독립 스케일링**이 이득인가?
   - **내결함성·가용성**이 중요한가?
3. **에이전트 경계 설정**: 각 에이전트를 *단일·원자적 책임*으로 정의하고, 입력/출력 계약과 실패 모드를 명시한다.
4. **책임·성공 기준 문서화**: 에이전트별 역할·권한·성공 기준(정량 지표)을 선언한다.

### 1.4 구현 예시 — 에이전트 분해와 정의 파일

에이전트를 분해할 때는 **정의(역할·책임·도구·경계)를 코드가 아닌 별도 파일(시스템 프롬프트 md)로 분리**합니다. 정의를 독립적으로 버전 관리·리뷰·재사용할 수 있고, 이는 Well-Architected의 *"에이전트 행동을 코드처럼 취급"* 원칙과 직결됩니다.

**프로젝트 구조 예시**

```text
agents/
├── orchestrator.md        # 라우팅·응답 종합
├── order_agent.md         # 주문 상태·반품·환불
├── product_agent.md       # 제품 추천
├── tech_support_agent.md  # 기술 지원
└── billing_agent.md       # 청구·결제
```

**에이전트 정의 파일 예시 — `agents/orchestrator.md`**

```markdown
# 오케스트레이터 에이전트

## 역할
당신은 전자상거래 고객 지원 **오케스트레이터**입니다. 사용자 요청을 분석해 알맞은 전문 에이전트에게 위임하고, 결과를 종합해 하나의 일관된 답변을 제공합니다. **직접 도메인 작업(주문 조회·환불·결제 등)을 수행하지 않습니다** — 항상 전문 에이전트를 통해 처리합니다.

## 사용 가능한 전문 에이전트 (도구)
| 에이전트 | 처리 범위 |
| --- | --- |
| `order_agent` | 주문 상태·배송·반품·환불 |
| `product_agent` | 제품 추천·비교·사양 |
| `tech_support_agent` | 사용법·오류·문제 해결 |
| `billing_agent` | 결제·청구·인보이스 |

## 라우팅 규칙
1. 사용자 요청에서 **의도(intent)** 를 파악한다.
2. 의도 → 에이전트 매핑:
   - 주문/배송/반품/환불 → `order_agent`
   - 제품 추천/비교/사양 → `product_agent`
   - 사용법/오류/고장 → `tech_support_agent`
   - 결제/청구/인보이스 → `billing_agent`
3. **다중 의도**: 한 요청에 여러 의도가 있으면 관련 에이전트를 각각 호출한 뒤 결과를 종합한다. (예: "주문 언제 와? 그리고 방수 모델 추천해줘" → order + product)
4. **모호한 의도**: 어느 에이전트인지 확신할 수 없으면 추측하지 말고 사용자에게 **명확화 질문**을 한다.
5. **범위 밖 요청**: 지원 범위를 벗어난 요청(법률 자문 등)은 정중히 거절하고 적절한 채널을 안내한다.

## 위임·컨텍스트 전달
- 전문 에이전트 호출 시 **필요한 컨텍스트만** 전달한다(전체 대화가 아니라 관련 요약 + 사용자 식별자).
- 이전 세션 정보가 필요하면 공유 메모리(`session_id`)에서 조회해 전달한다.

## 종합·충돌 해소
- 여러 에이전트 결과를 **중복 없이** 하나의 자연스러운 답변으로 통합한다.
- 결과가 상충하면 우선순위로 해소한다: **안전 > 규정 준수 > 정확성 > 고객 만족**.
- 각 정보의 출처(어느 에이전트)를 내부적으로 추적해 감사 가능성을 유지한다.

## 에스컬레이션 (휴먼 인 더 루프)
다음의 경우 자동 처리하지 말고 사람에게 에스컬레이션한다.
- 전문 에이전트가 HITL을 요구한 경우(예: 고액 환불, 사기 의심)
- 사용자가 명시적으로 상담원 연결을 요청한 경우
- 동일 문제를 2회 이상 시도했으나 해결되지 않은 경우

## 가드레일
- 개인정보(PII)·결제 정보를 응답에 노출하지 않는다.
- 확인되지 않은 정보를 지어내지 않는다("모름"을 인정하고 확인 경로 안내).
- 정책·가격·재고는 반드시 전문 에이전트의 실제 도구 결과에 근거한다.

## 응답 형식·톤
- 친근하고 간결한 존댓말. 핵심을 먼저, 세부는 뒤에 제시한다.
- 조치가 필요하면 다음 단계를 명확히 안내한다.

## 성공 기준
- 라우팅 정확도 ≥ 95%, 불필요한 에스컬레이션 최소화
- 최초 응답 해결률(FCR) ≥ 80%, 평균 처리 시간 목표 이내
```

**에이전트 정의 파일 예시 — `agents/order_agent.md`**

```markdown
# 역할
전자상거래 **주문 관리** 전문 에이전트. 주문 관련 문의를 정확하고 안전하게 처리한다.

## 책임 (단일·원자적)
- 주문 상태 조회 / 반품 접수 / 환불 처리

## 사용 가능한 도구
- `get_order_status(order_id)`
- `create_return(order_id, reason)`
- `issue_refund(order_id, amount)`   # $500 이하만 자동 처리

## 경계 및 핸드오프
- 결제·청구 문의 → `billing_agent`
- 제품 사용법·오류 → `tech_support_agent`
- 환불 $500 초과 또는 사기 의심 → **사람 검토(HITL)** 로 에스컬레이션

## 성공 기준
- 최초 응답 해결률 ≥ 90%, 정책 위반 0건
```

**정의 파일을 로드해 에이전트를 구성하는 코드 (Strands)**

```python
from pathlib import Path
from strands import Agent, tool
from strands.models import BedrockModel

# 1) 에이전트 정의(md)를 시스템 프롬프트로 로드한다.
#    정의를 코드에서 분리 → 프롬프트만 독립적으로 버전 관리·리뷰 가능("행동을 코드처럼 취급")
def load_prompt(name: str) -> str:
    return Path(f"agents/{name}.md").read_text(encoding="utf-8")

model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0")

# 2) 각 전문 에이전트를 '단일·원자적 책임'으로 생성한다(각자 필요한 도구만 보유).
order_agent = Agent(model=model, system_prompt=load_prompt("order_agent"),
                    tools=[get_order_status, create_return, issue_refund])
product_agent = Agent(model=model, system_prompt=load_prompt("product_agent"),
                      tools=[search_products])

# 3) "도구로서의 에이전트" 패턴: 전문 에이전트를 오케스트레이터의 '도구'로 래핑한다.
#    docstring은 오케스트레이터가 도구를 선택하는 근거가 되므로 명확히 작성한다.
@tool
def to_order_agent(query: str) -> str:
    """주문 상태·반품·환불 문의를 주문 관리 에이전트에 위임한다."""
    return str(order_agent(query))

@tool
def to_product_agent(query: str) -> str:
    """제품 추천·비교 문의를 제품 추천 에이전트에 위임한다."""
    return str(product_agent(query))

# 4) 오케스트레이터는 전문 에이전트(도구)들을 보유하고 '라우팅·종합'만 담당한다.
orchestrator = Agent(model=model, system_prompt=load_prompt("orchestrator"),
                     tools=[to_order_agent, to_product_agent])

# 5) 사용자 요청은 오케스트레이터로 진입 → 의도에 따라 적절한 전문 에이전트로 자동 위임된다.
answer = orchestrator("주문한 카메라 언제 도착해? 그리고 방수 되는 다른 모델도 추천해줘")
```

> **왜 정의 파일을 분리하는가**: 프롬프트·도구·역할이 코드에 하드코딩되면 리뷰·롤백·A/B 테스트가 어렵습니다. md 정의 파일은 Git 리뷰 대상이 되고, 배포 파이프라인에서 코드와 함께 일급 아티팩트로 관리됩니다(→ 모듈 5의 "다중 구성 요소 버전 관리").

각 에이전트는 자체 배포 파이프라인(개발→테스트→스테이징→프로덕션)을 갖고, 기능 추가·개선을 **독립적으로 새 버전으로 릴리스**합니다. 시스템 전체를 함께 재배포할 필요가 없고, 에이전트마다 서로 다른 버전이 동시에 운영될 수 있습니다(독립 배포성).

### 1.5 모범 사례 (Well-Architected Agentic AI Lens)

- 🏛️ **설계 원칙 "전문화·경계가 명확한 에이전트로 분해"**: 선언된 범위·명시적 한계·명확한 권한을 가진 단일 목적 에이전트가 평가·보안·확장·교체가 쉽다.
- 🏛️ **AGENTREL02-BP01 원자적 태스크 설계**: 에이전트를 구체적이고 원자적인 태스크로 설계하면 예측 가능성과 신뢰성이 올라간다.
- 🏛️ **AGENTREL01-BP02 모듈식·장애 격리 계층** / **AGENTREL01-BP03 액터 모델 기반 전문 에이전트**: 한 에이전트의 장애·버그가 다른 에이전트로 전파되지 않도록 격리한다.
- 🏛️ **AGENTSUS01-BP01 명시적 리소스 경계를 가진 전문 에이전트**: 지속 가능성 관점에서도 경계가 명확한 전문 에이전트가 리소스 효율이 높다.

---

## 파트 2. 에이전트 간 통신·오케스트레이션

### 2.1 해결할 문제

에이전트를 나눴다면, 이제 **어떻게 안전하고 신뢰성 있게 조정할 것인가**가 문제입니다. 고려 축은 결합도(coupling), 상태 관리, 오류 처리, 지연 시간, 재사용성, 보안입니다.

### 2.2 고려해야 할 기술·서비스·기능

#### (1) 3가지 통신 패턴 — 대부분의 시스템은 혼합 사용

| 패턴 | 동작 | 강점 | 언제 | 구현 |
| --- | --- | --- | --- | --- |
| **프레임워크 계층** | 중앙 오케스트레이션 계층이 라우팅·상태·복구를 관리 | 강력한 오류 처리·포괄적 상태 관리 | 신뢰성·유지 관리성이 우선인 엔터프라이즈 | Strands, LangGraph |
| **도구로서의 에이전트(Agent-as-Tools)** | 전문 에이전트를 호출 가능한 도구로 래핑, 느슨한 결합 | 재사용성·유연한 구성 | 여러 팀/사례에서 기능 공유 | MCP (Model Context Protocol) |
| **에이전트 간(A2A)** | 프레임워크 중재 없이 직접 P2P 통신 | 초저지연·자율 협업 | 플랫폼·조직 간 운영, 매우 짧은 지연 | Agent2Agent (A2A) 프로토콜 |

**도구로서의 에이전트 — 멀티 에이전트 Agentic Loop (ReAct)**

```ascii
사용자
  │
  │  1) 초기 요청
  v
┌─ 오케스트레이터 에이전트
│  컨텍스트와 실행 흐름을 유지하고, 라우팅과 종합만 담당한다
│
├──> 2) 데이터 검색 에이전트
├──> 3) 분석 에이전트
├──> 4) 통신 에이전트
│       세 에이전트는 필요하면 서로 직접 핸드오프한다
│
└──> 5) 사용자에게 최종 응답 (결과 종합)
```

A2A는 **에이전트 카드**(기능·엔드포인트·인증 요구를 알리는 JSON 메타데이터), **태스크 객체**(고유 ID·수명 주기), **아티팩트**(태스크 산출물) 개념으로 동작하며, AgentCore Runtime에서 A2A 서버를 호스팅할 수 있습니다.

#### (2) Strands 오케스트레이션 3종

| 방식 | 실행 흐름 | 컨텍스트 공유 | 오류 처리 | 적합한 문제 |
| --- | --- | --- | --- | --- |
| **워크플로** | 코드로 정의한 결정적 DAG(병렬·순차), 사이클 없음 | 태스크별 큐레이팅된 요약 | 다운스트림 즉시 중단 | 반복 가능·예측 가능한 프로세스(데이터 파이프라인, 온보딩) |
| **그래프** | 노드·엣지 기반, 조건 분기·순환(피드백 루프) 허용 | 전체 대화 공유 | 정의된 오류 엣지로 라우팅 | 분기 로직이 있는 구조화된 프로세스 |
| **스웜** | 에이전트가 자율적으로 핸드오프(창발적 지능) | 공유 작업 메모리 | 전문가 에이전트로 핸드오프 | 다분야 협업이 필요한 열린 문제 |

**Strands 오케스트레이션 3종 샘플 코드**

**① 워크플로 (Workflow)** — 결정적 DAG, 사이클 없음. 태스크와 종속성을 코드로 명시 → 예측 가능한 병렬·순차 실행.

```python
from strands import Agent
from strands.multiagent import Workflow

workflow = Workflow()
# 태스크 정의: 이름·담당 에이전트·(선택) 종속성
workflow.add_task("research", agent=research_agent)              # 독립 태스크 → 즉시 실행 가능
workflow.add_task("analysis", agent=analysis_agent,
                 depends_on=["research"])                        # research 완료 후 실행
workflow.add_task("report", agent=report_agent,
                 depends_on=["analysis"])                        # analysis 완료 후 실행

# 실행: 종속성 그래프에 따라 순서대로 처리. 독립 태스크는 병렬로 실행 가능.
wf_result = workflow.run("연간 보고서를 작성하라")
```

**② 그래프 (Graph)** — 노드·엣지 기반, 조건 분기·피드백 루프 허용. LLM이 실행 경로를 결정하는 동적·구조적 흐름.

```python
from strands import Agent
from strands.multiagent import GraphBuilder

builder = GraphBuilder()
builder.add_node(research_agent, "research")       # 노드 = 에이전트 (중첩 그래프/스웜도 가능)
builder.add_node(analysis_agent, "analysis")
builder.add_node(fact_check_agent, "fact_check")
builder.add_node(report_agent, "report")

builder.add_edge("research", "analysis")           # 엣지 = 데이터 흐름 (앞 노드 출력 → 뒤 노드 입력)
builder.add_edge("analysis", "fact_check")
builder.add_edge("fact_check", "report")
builder.add_edge("fact_check", "analysis")         # ← 피드백 루프: 팩트체크 실패 시 분석 재실행

graph = builder.build()
# invocation_state: 모든 노드가 공유하는 실행 컨텍스트
graph_result = graph("고객 데이터 분석 리포트를 작성하라",
                     invocation_state={"session_id": "sess-001"})
```

**③ 스웜 (Swarm)** — 사전 정의 경로 없이 자율 핸드오프. 각 에이전트가 자체 판단으로 다음 에이전트에게 바톤을 넘김(창발적 지능).

```python
from strands import Agent
from strands.multiagent import Swarm

swarm = Swarm(
    agents=[coder_agent, architect_agent, reviewer_agent],  # 참여 에이전트 풀
    # 모든 에이전트가 공유 작업 메모리에 접근하며 협업
)
# 실행: 첫 에이전트부터 시작해 핸드오프를 반복, 태스크 완료 시 종료
swarm_result = swarm("결제 모듈을 설계·구현·코드 리뷰하라",
                     invocation_state={"user_id": "dev-42", "debug": True})
# 결과: 마지막 활성 에이전트의 출력 (중간 핸드오프 이력은 공유 메모리에 기록)
```

> **💡 패턴 선택 팁**: 실행이 완전히 결정적이어야 하면 워크플로, 조건 분기·반복 개선이 필요하면 그래프, 경로를 미리 정할 수 없는 협업이면 스웜. 지연·신뢰성·보안 요구에 따라 패턴을 혼합 사용합니다.

### 2.3 구현 요건 및 절차

**A. 통신 인터페이스 표준화 (모든 패턴 공통 선행 작업)**
1. 각 에이전트의 **입력/출력 형식**을 정의한다.
2. **오류 처리 프로토콜**을 정의한다(재시도·타임아웃·폴백).
3. **데이터 스키마 · 인증 요구 · 응답 형식 사양**을 생성하고 버전을 관리한다.

**B. "도구로서의 에이전트" 를 AgentCore Gateway로 노출하는 절차**
1. 전문 에이전트/도구를 **대상(target)** 으로 등록한다 (Lambda / OpenAPI / Smithy / MCP).
2. **인바운드 인증**을 선택한다: IAM SigV4(AWS 주체) 또는 OAuth 토큰(MCP 권한 부여 사양, 최종 사용자 위임).
3. **아웃바운드 권한 부여**를 구성한다: IAM / API 키 / OAuth 토큰(클라이언트 자격 증명 또는 권한 부여 코드).
4. Gateway가 `도구 나열·간접 호출·검색`을 표준화하므로, 오케스트레이터는 이 인터페이스만 알면 된다.

**C. 오케스트레이션 패턴 선택 절차**
1. 실행이 **완전히 결정적**이어야 하면 → 워크플로.
2. **조건 분기·반복 개선**이 필요하면 → 그래프.
3. **경로를 미리 정할 수 없는 협업**이면 → 스웜.
4. 지연·신뢰성·보안 요구에 따라 패턴을 **혼합**한다.

### 2.4 구현 예시

**프레임워크 계층 & 도구로서의 에이전트 다이어그램**

```ascii
┌─ AgentCore Runtime (프레임워크 계층)
│
├──> 문서 처리 에이전트
├──> 청구 에이전트
├──> 기술 지원 에이전트
│       세 에이전트는 런타임을 통해 서로 통신한다
│       직접 연결하지 않으므로 한쪽 장애가 다른 쪽으로 전파되지 않는다
│
└─ 런타임이 대신 처리하는 것
     - 에이전트 간 조정
     - 실행 컨텍스트 지속성
     - 상태 관리
     - 오류 복구
     - 성능 모니터링
```

**A2A(에이전트 간) 다이어그램**

```ascii
사용자
  │
  v
┌─ 로컬 에이전트 (A2A 클라이언트)
│
├──> 원격 에이전트 A (A2A 서버)
│      에이전트 카드로 기능 / 엔드포인트 / 인증 요구를 공개
│      태스크를 처리하고 아티팩트를 반환
│
├──> 원격 에이전트 B (A2A 서버)
│      에이전트 카드로 기능 / 엔드포인트 / 인증 요구를 공개
│      태스크를 처리하고 아티팩트를 반환
│
└─ 프레임워크 중재 없이 직접 P2P 통신 (초저지연 / 자율 협업)
     중앙 제어를 우회하므로 메시지 암호화와 신뢰 경계 설정이 필수
```

### 2.5 모범 사례 (Well-Architected Agentic AI Lens)

- 🏛️ **AGENTREL04-BP01 arbiter(중재자) 패턴 (핵심)**: 오케스트레이터가 *모든* 메시지를 중재하면 단일 병목·장애점이 된다. 대규모·고신뢰 시스템에서는 **충돌 조정이 필요할 때만 이벤트 기반으로 활성화되는 전담 arbiter**를 두고, 전문 에이전트는 독립 실행한다.
- 🏛️ **AGENTREL04-BP02 역량 분류(capability taxonomy) + AgentCore Registry**: 하드코딩된 에이전트 ID 대신 구조화된 역량 메타데이터 + 시맨틱 검색으로 결정적 라우팅하고, 에이전트 교체 시 자동 대체한다.
- 🏛️ **AGENTREL04-BP03 폴백 체인 / AGENTREL04-BP04 복원력 있는 제어 평면**: 각 핵심 에이전트에 순서 있는 폴백 체인을 두고, 제어 평면 자체를 중복·내구성 있게 만든다.
- 🏛️ **AGENTOPS04-BP02 표준 통합 프로토콜(MCP·A2A)** / **AGENTPERF04 효율적 프로토콜 통신** / **AGENTPERF05 오케스트레이션·협업 성능**.
- 🏛️ **AGENTSEC06 오케스트레이션 보안**: A2A 직접 통신은 중앙 제어를 우회하므로 **에이전트 간 메시지 암호화·서명(BP01)**, **신뢰 경계 설정(BP03)** 이 필수다. (상세는 모듈 3)

---

## 파트 3. 메모리 및 상태 관리

### 3.1 해결할 문제

단일 에이전트는 자체 컨텍스트만 유지하면 되지만, 다중 에이전트에서는 **컨텍스트 단편화 · 상태 동기화 · 일관성 · 메모리 수명 주기**가 핵심 난제입니다. 메모리 요구량은 에이전트 수·상호작용 복잡도에 따라 급증합니다.

에이전트 메모리는 세 가지 목적을 수행합니다 — **컨텍스트 인텔리전스**(현재 세션 흐름 유지), **사용자 선호**(개인화), **지식 보존**(세션 간 사실·관계 축적).

### 3.2 고려해야 할 기술·서비스·기능

| 접근 | 특징 | 언제 |
| --- | --- | --- |
| **AgentCore Memory** | 서버리스, 단기(원시 이벤트)·장기(추출된 레코드) 이중 구조, 네임스페이스, 유동적 TTL, 암호화 기본 | 기본 세션 공유·개인화 |
| **Strands SDK 상태** | `invocation_state`로 그래프·스웜 전반에 상태 전파, 대화 관리·요약 | 정교한 대화 관리 |
| **외부 스토리지** | DynamoDB/ElastiCache/OpenSearch 등, 기존 시스템 통합 | 기업 DB 연동·규정 준수·비-에이전트 시스템 공유 |

**AgentCore Memory 핵심 동작**
- 단기 메모리: `actorId` + `sessionId`별 이벤트로 저장. `ListSessions`/`ListEvents`/`GetEvent`로 접근.
- 장기 메모리: 백그라운드에서 **비동기 추출**(요약·사실·지식·선호). `GetMemoryRecord`/`ListMemoryRecords`/`RetrieveMemoryRecords`(시맨틱 검색)로 접근.

```ascii
┌─ 에이전트 (대화 실행)
│
├─ 쓰기: CreateEvent 로 매 상호작용을 기록
│  │
│  v
│  ┌─ 단기 메모리
│  │  원시 이벤트를 그대로 저장
│  │  ListSessions / ListEvents / GetEvent 로 조회
│  │
│  └─ 비동기 추출 (백그라운드에서 실행, 라이브 대화를 막지 않는다)
│     │
│     v
│     ┌─ 장기 메모리
│     │  요약 / 사실과 지식 / 사용자 선호만 남긴다
│     │  GetMemoryRecord / ListMemoryRecords 로 조회
│     └─ RetrieveMemoryRecords 로 시맨틱 검색
│
└─ 읽기: 전체 기록 대신 관련 기억만 골라 프롬프트에 주입
```

### 3.3 구현 요건 및 절차

**A. 공유 메모리 아키텍처 설계 절차**
1. **정보 분류**: 무엇을 단기(원시 대화)로, 무엇을 장기(선호·사실·요약)로 둘지 분류한다.
2. **네임스페이스 설계**: 예) `/preferences/{actorId}/`, `/facts/{actorId}/`, `/summaries/{actorId}/{sessionId}/` 로 격리·조직화한다. **끝에 슬래시를 붙입니다** — 없으면 멀티테넌트에서 접두사 충돌이 생깁니다(`/actors/Alice/` 가 맞고 `/actors/Alice` 는 위험).
3. **공유 규칙 정의**: 모든 에이전트가 동일 `memory_id` + 동일 `session_id`를 공유합니다. **`actor_id`는 두 갈래로 갈립니다** — 단기 이벤트를 에이전트별로 격리하려면 에이전트마다 고유한 `actor_id`를 쓰고, 장기 기억을 에이전트 간에 **공유**하려면 `actor_id`를 최종 사용자로 통일하거나 네임스페이스에서 `{actorId}`를 빼야 합니다. 장기 공유는 `actor_id`가 아니라 **네임스페이스 템플릿**이 결정합니다(→ 3.4 "장기 메모리를 여러 에이전트가 공유하기").
4. **성능 최적화**: 전체 기록 대신 **요약을 공유**하고, 비용 큰 작업은 **지연 로딩**한다.
5. **점진적 성능 저하 설계**: 메모리 접근 실패 시 완전 실패가 아니라 축소된 컨텍스트로 계속 동작하게 한다.

**B. Strands 메모리 후크 공유 절차**
1. `session_manager.create_memory_session(actor_id, session_id)` 로 에이전트별 메모리 세션을 만든다.
2. `ShortTermMemoryHook(memory_session, memory_id)` 를 각 에이전트의 `hooks`에 연결한다.
3. 오케스트레이터가 "도구로서의 에이전트" 로 각 전문 에이전트를 호출하면, 후크가 자동으로 공유 메모리에 이벤트를 적재한다.

### 3.4 구현 예시

**다중 에이전트 공유 메모리 구조**

```ascii
┌─ 오케스트레이터
│
├──> 제품 반품 에이전트
│      actor_id: returns
│      메모리 후크가 이벤트를 자동 적재하고 과거 컨텍스트를 자동 주입
│
├──> 제품 정보 에이전트
│      actor_id: product
│      메모리 후크가 이벤트를 자동 적재하고 과거 컨텍스트를 자동 주입
│
└──> AgentCore Memory (두 에이전트가 공유)
       단기 : 반품 / 조회 이벤트
       장기 : 사용자 선호 / 세션 요약

       memory_id  : 공유 (같은 메모리 리소스를 쓴다)
       session_id : 공유 (같은 대화 컨텍스트로 묶인다)
       actor_id   : 에이전트별로 다르게 (개별 자격 증명을 유지한다)
```

**Strands 단기 메모리 공유 (에이전트별 actor_id)**

```python
def product_info_agent(query: str) -> str:
    try:
        # 메모리 세션 생성:
        #  - actor_id: 에이전트별 고유값 → 개별 자격 증명·네임스페이스 분리
        #  - session_id: 모든 에이전트가 공유 → 같은 대화 컨텍스트로 묶음
        memory_session = session_manager.create_memory_session(
            actor_id=PRODUCT_INFO_ACTOR_ID,
            session_id=SESSION_ID,
        )
        # 메모리 후크: 매 상호작용을 단기 메모리에 이벤트로 자동 적재하고,
        # 관련 과거 컨텍스트를 프롬프트에 자동 주입한다(수동 관리 불필요)
        hooks = ShortTermMemoryHook(memory_session, memory_id)
        agent = Agent(
            hooks=[hooks],                       # 후크를 연결해야 공유 메모리에 기록/조회됨
            model=MODEL_ID,
            system_prompt=PRODUCT_INFO_PROMPT,   # agents/product_agent.md 등에서 로드한 정의
            state={"actor_id": PRODUCT_INFO_ACTOR_ID, "session_id": SESSION_ID},
        )
        return str(agent(query))                 # 에이전트 실행 → 응답 문자열 반환
    except Exception as e:
        # 메모리/모델 오류 시 전체 실패 대신 오류 메시지 반환(점진적 성능 저하)
        return f"Error in product info agent: {e}"
```

**공유 상태·도구 컨텍스트 전파 (`invocation_state`)**

```python
# 오케스트레이션 진입 시 공유 상태를 한 번만 정의하면 모든 노드·도구로 전파된다.
shared_state = {"user_id": "user123", "session_id": "sess456", "debug_mode": True}
result = graph("Analyze customer data", invocation_state=shared_state)

from strands import tool, ToolContext

@tool(context=True)                              # context=True → 도구가 ToolContext를 받음
def query_data(query: str, tool_context: ToolContext) -> str:
    # invocation_state에서 공유 값을 꺼내 개인화·분기 처리에 사용
    user_id = tool_context.invocation_state.get("user_id")
    debug = tool_context.invocation_state.get("debug_mode", False)
    # invocation_state는 도구 및 도구 후크(BeforeToolCallEvent 등)로 자동 전파됨
    return run_personalized_query(query, user_id=user_id, debug=debug)
```

**장기 메모리를 여러 에이전트가 공유하기 — 네임스페이스 설계**

앞의 단기 메모리 예시는 `memory_id`·`session_id`를 공유하고 `actor_id`만 에이전트별로 다르게 뒀습니다. 단기 메모리는 이벤트가 `(actorId, sessionId)` 조합으로 저장되므로, 이 방식이 곧 "같은 대화 안에서 에이전트별 격리"가 됩니다.

**그런데 장기 메모리에는 이 방식이 그대로 통하지 않습니다.** 장기 메모리는 전략(strategy)의 `namespaceTemplates`가 정한 **네임스페이스**로 추출되는데, 템플릿에 `{actorId}`가 들어 있고 에이전트마다 `actor_id`가 다르면 서로 다른 네임스페이스가 만들어져 **공유가 깨집니다.** 즉 장기 메모리 공유는 `actor_id` 문제가 아니라 **네임스페이스 설계 문제**입니다.

```ascii
[문제]  에이전트별 actor_id 를 쓰면 장기 메모리가 갈라진다

전략 네임스페이스 템플릿:  /facts/{actorId}/

┌─ 제품 반품 에이전트   actor_id = returns-agent
│    추출 결과 --> /facts/returns-agent/
│
├─ 제품 정보 에이전트   actor_id = product-agent
│    추출 결과 --> /facts/product-agent/
│
└─ 두 네임스페이스는 서로 보이지 않는다  =>  공유되지 않는다


[해결 A]  actor_id 를 '최종 사용자' 로 통일한다  (권장)

전략 네임스페이스 템플릿:  /facts/{actorId}/   actor_id = customer-42

┌─ 제품 반품 에이전트   쓰기 --> /facts/customer-42/
├─ 제품 정보 에이전트   쓰기 --> /facts/customer-42/
└─ 기술 지원 에이전트   읽기 <-- /facts/customer-42/

     어느 에이전트가 남긴 기억인지는 이벤트 메타데이터로 구분한다


[해결 B]  네임스페이스에서 {actorId} 를 빼고 공유 축으로 스코프한다

전략 네임스페이스 템플릿:  /tenant/{tenantname}/customer/{customerid}/

┌─ actor_id 는 에이전트별로 유지한다
└─ 추출 결과는 커스텀 변수가 정한 공유 네임스페이스로 모인다
```

**해결 A가 문서의 표준 예시와 맞는 방향입니다.** AgentCore 문서는 액터를 *"최종 사용자 또는 에이전트/사용자 조합"* 으로 정의하며, 코딩 지원 챗봇의 액터는 질문하는 개발자라고 설명합니다. 즉 `actorId`는 원래 "누구의 기억인가"를 가리키는 축이고, "어느 에이전트가 만들었는가"를 넣을 자리가 아닙니다.

**네임스페이스 세분화 4단계**

| 템플릿 | 공유 범위 |
| --- | --- |
| `/strategy/{memoryStrategyId}/actor/{actorId}/session/{sessionId}/` | 한 액터의 그 세션만 |
| `/strategy/{memoryStrategyId}/actor/{actorId}/` | 한 액터의 모든 세션 |
| `/strategy/{memoryStrategyId}/` | **액터를 넘어 전략 전체** |
| `/` | 모든 전략 전체 |

빌트인 변수는 `actorId`·`sessionId`·`memoryStrategyId` 세 개입니다. 테넌트·팀·환경처럼 다른 축이 필요하면 **커스텀 네임스페이스 변수**를 메모리 리소스당 최대 5개까지 정의할 수 있습니다(값은 모두 소문자).

**1) 공유 네임스페이스를 가진 메모리 리소스 생성**

```python
from bedrock_agentcore.memory import MemoryClient

client = MemoryClient(region_name="us-east-1")

# 전략마다 네임스페이스 템플릿을 따로 준다 → 공유 범위를 전략별로 다르게 설계한다.
memory = client.create_memory_and_wait(
    name="SharedCustomerSupportMemory",
    description="고객 지원 에이전트들이 공유하는 장기 메모리",
    strategies=[
        {
            # 세션 요약: {sessionId}까지 넣어 세션별로 분리 (세션 단위 회고용)
            "summaryMemoryStrategy": {
                "name": "SessionSummarizer",
                "namespaceTemplates": ["/summaries/{actorId}/{sessionId}/"],
            }
        },
        {
            # 사용자 선호: {sessionId} 없음 → 세션을 넘어 누적·공유된다
            "userPreferenceMemoryStrategy": {
                "name": "PreferenceLearner",
                "namespaceTemplates": ["/preferences/{actorId}/"],
            }
        },
        {
            # 사실·지식: 세션을 넘어 공유
            "semanticMemoryStrategy": {
                "name": "FactExtractor",
                "namespaceTemplates": ["/facts/{actorId}/"],
            }
        },
    ],
)
MEMORY_ID = memory["id"]
# 주의: 전략이 ACTIVE 가 된 '이후'에 생성된 이벤트만 장기 추출 대상이다.
#       나중에 전략을 추가해도 그 전 대화는 소급 추출되지 않는다.
```

**2) 여러 에이전트가 같은 장기 네임스페이스를 읽도록 구성 (Strands)**

```python
from strands import Agent
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig,
    PersistenceMode,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)

CUSTOMER_ID = "customer-42"           # actor_id = 최종 사용자 (에이전트가 아니다)
SESSION_ID = "sess-2026-07-02-001"    # 같은 대화로 묶는 축

# 읽을 장기 네임스페이스를 '네임스페이스 -> 검색 설정' 딕셔너리로 선언한다.
# 키에 {actorId}/{sessionId}/{memoryStrategyId} 를 쓰면 그 에이전트의 config 값으로
# 치환되고, 조회는 계층(prefix) 검색으로 수행된다. 여러 개를 넣으면 병렬 조회 후
# 결과를 함께 프롬프트에 주입한다. 한 네임스페이스 조회가 실패해도 나머지는 진행된다.
SHARED_NAMESPACES = {
    "/preferences/{actorId}/": RetrievalConfig(top_k=5, relevance_score=0.3),
    "/facts/{actorId}/": RetrievalConfig(top_k=10, relevance_score=0.3),
}


def build_agent(agent_name: str, system_prompt: str, *, read_only: bool = False) -> Agent:
    """같은 고객(actor_id)의 장기 메모리를 공유하는 에이전트를 만든다."""
    config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID,
        session_id=SESSION_ID,
        actor_id=CUSTOMER_ID,              # 핵심: 에이전트별 값이 아니라 고객 값
        retrieval_config=SHARED_NAMESPACES,
        # actor_id 를 공유했으므로, 출처 추적은 이벤트 메타데이터로 한다.
        default_metadata={"agent": agent_name},
        # 읽기 전용 소비자는 쓰기를 끈다. 장기 메모리 주입은 그대로 동작한다.
        persistence_mode=PersistenceMode.NONE if read_only else PersistenceMode.FULL,
    )
    return Agent(
        system_prompt=system_prompt,
        session_manager=AgentCoreMemorySessionManager(config, region_name="us-east-1"),
    )


returns_agent = build_agent("returns", RETURNS_PROMPT)
product_agent = build_agent("product", PRODUCT_PROMPT)
# 기술 지원은 조회만 한다 → 공유 기억은 읽지만 새 이벤트는 남기지 않는다
support_agent = build_agent("support", SUPPORT_PROMPT, read_only=True)
```

**3) 프레임워크 없이 직접 검색 — 정확 일치 vs 계층 검색**

```python
from bedrock_agentcore.memory.session import MemorySessionManager

session_manager = MemorySessionManager(memory_id=MEMORY_ID, region_name="us-east-1")
session = session_manager.create_memory_session(
    actor_id=CUSTOMER_ID,      # 공유 축
    session_id=SESSION_ID,
)

# (1) namespace: '정확히 그 네임스페이스' 하나만 검색
prefs = session.search_long_term_memories(
    namespace=f"/preferences/{CUSTOMER_ID}/",
    query="고객이 선호하는 제품 조건은?",
    top_k=5,
)

# (2) namespace_path: '그 아래 계층 전체' 를 검색
#     세션별로 쪼개 저장한 요약을 세션 경계를 넘어 한 번에 훑을 때 쓴다.
history = session.search_long_term_memories(
    namespace_path=f"/summaries/{CUSTOMER_ID}/",
    query="지난 문의에서 어떤 문제가 있었나?",
    top_k=5,
)
# 이 두 호출은 어느 에이전트에서 실행해도 같은 결과를 준다.
# 검색은 '내 actor_id' 가 아니라 '내가 지정한 네임스페이스' 를 기준으로 하기 때문이다.
```

**주의할 점**

- **비동기 추출 지연**: 이벤트를 쓴 직후에는 장기 메모리에 없습니다. 추출·통합이 백그라운드로 돌기 때문에 1분 이상 걸릴 수 있으므로, 방금 쓴 내용을 즉시 읽는 흐름을 만들지 마세요.
- **전략 활성화 시점**: 전략이 `ACTIVE`가 된 이후 이벤트만 추출됩니다. 운영 중에 전략을 추가하면 과거 대화는 비어 있습니다.
- **커스텀 변수 누락은 조용히 실패합니다**: 전략 템플릿이 참조하는 커스텀 변수를 `CreateEvent`에서 주지 않으면 그 전략의 추출만 건너뛰어지고 `CreateEvent` 자체는 성공합니다. `NamespaceResolutionFailure` 지표로 감시하세요.
- **공유 범위가 곧 폭발 반경**: 네임스페이스를 넓히면 한 에이전트가 오염시킨 기억이 전원에게 퍼집니다. IAM 조건 키로 좁히세요 — 읽기는 `bedrock-agentcore:namespace`(정확 일치)·`bedrock-agentcore:namespacePath`(계층), 쓰기는 `bedrock-agentcore:namespaceVariable/<키>`. (→ 모듈 3의 AGENTSEC01 메모리 격리·무결성)
- **전략별로 공유 범위를 다르게 두세요**: 위 예시처럼 요약은 세션별로 좁히고 선호·사실만 세션을 넘어 공유하는 편이, 전부 공유하는 것보다 오염 위험과 검색 노이즈가 낮습니다.

**종합 시나리오 — 세션·에이전트를 넘나드는 컨텍스트 연속성**
> 고객 Sofia가 세션 1에서 "300달러 미만 방수 카메라"를 문의 → 제품 추천 에이전트가 선호를 장기 메모리에 저장(`/preferences`). 세션 2에서 주문 관리 에이전트가 동일 네임스페이스를 검색해 "다이빙 여행 예정"을 인지하고 선제 응답. 세션 3에서 기술 지원 에이전트가 "AquaPro 200 구매·다이빙 목적"을 확인해 맞춤 문제 해결. → 4개 에이전트가 **수동 핸드오프·재질문 없이** 컨텍스트를 공유.

### 3.5 모범 사례 (Well-Architected Agentic AI Lens)

- 🏛️ **AGENTREL03 메모리·상태 신뢰성**: 정보 분류 모델(BP01), 중복·페일오버 있는 내결함성 메모리 스토어(BP02), 체크포인트 기반 복구(BP03), 메모리 작업의 점진적 성능 저하(BP04).
- 🏛️ **AGENTPERF03-BP01 계층형 메모리**: 세션 읽기(핫)와 장기 시맨틱 쿼리를 같은 백엔드에서 경쟁시키지 말고 접근 패턴에 스토리지를 맞춘다.
- 🏛️ **AGENTSEC01 메모리·상태 보안**: 메모리 격리·무결성(BP01), 입력 검증·소독(BP02), 환각 전파 모니터링(BP03). 저장 시 AES-256·전송 시 TLS, 멀티테넌트는 행 수준 격리.

---

## 파트 4. 프로덕션 구현 종합 체크리스트

파트 1~3에서 만든 시스템을 프로덕션에 올릴 때 반드시 점검합니다.

- **관찰성 우선 설계**: 시스템이 단순할 때 로깅·추적을 심는다(나중 추가보다 쉽다). 모든 메모리·통신 작업의 접근 패턴·성능·오류율을 기록. (→ 모듈 4)
- **장애 대비**: 이중화·점진적 성능 저하·회로 차단기·복구 패턴을 구현한다(가용성 목표 예: 99.9% 초과).
- **보안**: 최소 권한 IAM 역할, 에이전트 간 인증·신뢰 경계, 암호화. (→ 모듈 3)
- **확장성**: 수평 스케일을 전제로 설계. AgentCore Runtime의 자동 스케일·세션 격리 활용.
- **명확한 인터페이스·문서화**: 통신 계약을 문서화하고 이전 버전과의 호환성을 관리한다.
- **간단하게 시작 → 반복**: 최소 구성으로 시작해 근거를 확인하며 에이전트를 늘린다.

---

## Well-Architected Agentic AI Lens 매핑 (요약 레퍼런스)

> 기준: [AWS Well-Architected Agentic AI Lens](https://docs.aws.amazon.com/ko_kr/wellarchitected/latest/agentic-ai-lens/agentic-ai-lens.html) (2026-06-10). 본문 각 파트의 🏛️ 표시가 해당 모범 사례이며, 아래는 매핑·보완 요약입니다.

| 본 모듈 주제 | 관련 모범 사례(BP) |
| --- | --- |
| 에이전트 분해·경계 (파트 1) | 설계 원칙 1, AGENTREL02-BP01, AGENTREL01-BP02/03, AGENTSUS01-BP01 |
| 통신 패턴 (파트 2) | AGENTOPS04-BP02, AGENTPERF04, AGENTSEC06 |
| 오케스트레이션 (파트 2) | AGENTREL04-BP01~04, AGENTPERF05, AGENTCOST01-BP03 |
| 메모리·상태 (파트 3) | AGENTREL03, AGENTPERF03-BP01, AGENTSEC01 |
