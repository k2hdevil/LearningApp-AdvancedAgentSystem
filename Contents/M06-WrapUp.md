# 모듈 6 · 참고 자료 및 공식 문서

> Building Advanced Agentic Systems on AWS (한국어) · 300레벨 심화
> 이 자료를 만들며 각 모듈에서 참조·검증한 AWS 공식 문서, 레퍼런스 아키텍처, SDK 문서를 모듈별로 정리했습니다.
> 본문의 서술은 아래 문서를 기준으로 교차 검증했습니다. 시험·실무 적용 전에는 항상 최신 원문을 확인하세요.

---

## 과정 전체를 관통하는 기준 문서

에이전틱 워크로드 설계·검토의 1차 기준입니다. 모든 모듈의 🏛️ 모범 사례 표시가 이 렌즈를 근거로 합니다.

- **[AWS Well-Architected Agentic AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentic-ai-lens.html)** — 6개 기둥 · 41개 질문 · 150개 모범 사례. 에이전틱 AI 여정 단계별 읽기 경로(Lens 로드맵) 포함.
- **[Agentic AI Lens — 부록 A: 모범 사례 레퍼런스](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/appendix-a.html)** — AGENTOPS·AGENTSEC·AGENTREL·AGENTPERF·AGENTCOST·AGENTSUS 전체 BP 목록과 위험 등급.
- **[AWS Well-Architected 사용자 지정 렌즈 GitHub](https://github.com/aws-samples/sample-well-architected-custom-lens)** — Agentic AI Lens JSON을 AWS Well-Architected Tool로 가져와 실제 워크로드를 검토할 수 있습니다.
- **[Strands Agents SDK 문서](https://strandsagents.com/docs/)** — 본 과정의 코드 예제가 사용하는 오픈소스 에이전트 프레임워크.
- **[Amazon Bedrock AgentCore 개발자 안내서](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)** — Runtime · Memory · Gateway · Identity · Observability · Evaluations 전반.

---

## 모듈 1 · 다중 에이전트 아키텍처 및 통신 패턴

**AgentCore 런타임·메모리**
- [AgentCore Runtime 작동 방식](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html) — 세션별 전용 microVM 격리, 서버리스 실행.
- [AgentCore Runtime 세션 격리](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-sessions.html) — 세션 수명 주기와 격리 모델.
- [AgentCore Memory 개요](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html) 및 [메모리 유형](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-types.html) — 단기/장기 메모리, 비동기 추출.
- [AgentCore Memory API](https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/) — `CreateEvent` · `ListSessions` · `ListEvents` · `GetEvent` · `GetMemoryRecord` · `ListMemoryRecords` · `RetrieveMemoryRecords`.

**통신 프로토콜**
- [AgentCore Gateway 핵심 개념](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-core-concepts.html) — MCP 도구 노출, 대상(target) 유형.
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) — "도구로서의 에이전트" 패턴의 개방형 표준.
- [Agent2Agent (A2A) 프로토콜](https://a2a-protocol.org/) — 에이전트 간 직접 통신, 에이전트 카드.

**모범 사례**: 신뢰성 [AGENTREL04(다중 에이전트 오케스트레이션)](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentrel04.html), 성능 [AGENTPERF05](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentperf05.html).

---

## 모듈 2 · 컨텍스트 엔지니어링 및 성능 최적화

**토큰·비용**
- [Amazon Bedrock 토큰 계산 방식](https://docs.aws.amazon.com/bedrock/latest/userguide/quotas-token-burndown.html) — `max_tokens` 동작, TPM/TPD 선점·정산, 출력 토큰 번다운 배율.
- [Amazon Bedrock 프롬프트 캐싱](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html) — 캐시 체크포인트, TTL, `CacheReadInputTokens`/`CacheWriteInputTokens`.
- [Amazon Bedrock 요금](https://aws.amazon.com/bedrock/pricing) — 토큰 비용 산정.

**메모리·검색**
- [장기 메모리 네임스페이스 조직](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/specify-long-term-memory-organization.html) — 네임스페이스 4단계 세분화, 커스텀 변수, IAM 조건 키.
- [인사이트 저장·검색](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/long-term-saving-and-retrieving-insights.html) — `search_long_term_memories`의 `namespace` vs `namespace_path`.
- [Strands + AgentCore Memory 통합](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/strands-sdk-memory.html) — `AgentCoreMemorySessionManager`, 전략별 `namespaceTemplates`.

**입력 형식·전략**
- [LangChain — 에이전트를 위한 컨텍스트 엔지니어링](https://blog.langchain.com/context-engineering-for-agents) — 5대 전략(입력 형식·기록·선택·압축·분리) 분류의 출처.
- [TOON (Token-Oriented Object Notation)](https://github.com/toon-format/toon) — 입력 형식 최적화 예시.
- [Strands Bedrock 모델 프로바이더 — 캐싱](https://strandsagents.com/docs/user-guide/concepts/model-providers/amazon-bedrock/#caching) — 프레임워크 수준 캐싱 설정.

**모범 사례**: 성능 [AGENTPERF03(메모리·컨텍스트·RAG)](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentperf03.html), 비용 [AGENTCOST02](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentcost02.html)·[AGENTCOST03](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentcost03.html).

---

## 모듈 3 · 보안 및 규정 준수 구현

**위협 모델·프레임워크**
- [Agentic AI Security Scoping Matrix](https://aws.amazon.com/blogs/security/the-agentic-ai-security-scoping-matrix-a-framework-for-securing-autonomous-ai-systems/) — 자율성 4범위, 6가지 보안 차원.
- [OWASP Top 10 for LLM & 에이전틱 AI](https://genai.owasp.org/) — 10대 위협.
- [AWS 심층 방어(Defense in Depth)](https://docs.aws.amazon.com/whitepapers/latest/aws-overview/security-and-compliance.html) — 7계층 보안.

**자격 증명·정책**
- [Amazon Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/) · [AWS IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/) — 사용자·리소스 인증.
- [AgentCore Gateway 인바운드/아웃바운드 인증](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-inbound-auth.html) — SigV4/OAuth, IAM/API 키/OAuth.
- [Cedar 정책 언어](https://www.cedarpolicy.com/) — `permit`/`forbid`, 조건부 정책.
- [OAuth 2.0 (RFC 6749)](https://datatracker.ietf.org/doc/html/rfc6749) — 2LO/3LO 흐름.

**네트워크 격리**
- [AWS PrivateLink](https://docs.aws.amazon.com/vpc/latest/privatelink/) · [VPC 인터페이스 엔드포인트](https://docs.aws.amazon.com/vpc/latest/privatelink/create-interface-endpoint.html) — 프라이빗 연결.
- [교차 계정 메모리 액세스](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-cross-account-access.html) — 리소스 기반 정책, 메모리 실행 역할.

**규정 준수**
- [AWS Well-Architected Responsible AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/responsible-ai-lens/responsible-ai-lens.html) — 책임 있는 AI 수명 주기·차원.

**모범 사례**: 보안 [AGENTSEC01~09](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/appendix-a.html) (메모리·도구·자격 증명·목표 정렬·관찰성·오케스트레이션·인간 감독·입출력·취약점 스캔).

---

## 모듈 4 · 프로덕션 모니터링, 관찰성 및 평가

**관찰성**
- [AgentCore Observability](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability.html) — 세션·트레이스·스팬 3계층 모델.
- [OpenTelemetry](https://opentelemetry.io/docs/) — 공급업체 중립 원격 측정 표준.
- [AWS Distro for OpenTelemetry (ADOT)](https://aws-otel.github.io/docs/introduction) — OTel의 AWS 배포판.
- [Amazon CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/) · [Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-transaction-search.html) — 지표·로그·트레이스 저장·조회.

**평가**
- [AgentCore Evaluations](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/) — 13개 내장 평가기, 온라인/온디맨드 모드.
- [Strands Evaluations SDK](https://strandsagents.com/docs/user-guide/evals-sdk/quickstart/) — 데이터세트 기반 평가.

**모범 사례**: 운영 우수성 [AGENTOPS05(관찰성)](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentops05.html), [AGENTOPS06(테스트·평가·검증)](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentops06.html).

---

## 모듈 5 · Well-Architected 에이전틱 AI 시스템

- [AWS Well-Architected Agentic AI Lens — 설계 원칙](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/design-principles.html) — 5가지 설계 원칙.
- [Agentic AI Lens — 부록 A](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/appendix-a.html) — 6개 기둥 · 41개 질문 · 150개 BP 전체.
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) — 기본 6기둥 (렌즈의 토대).
- [AWS Well-Architected Generative AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html) — 기반 모델 관점의 보완 렌즈.
- [AWS Well-Architected Responsible AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/responsible-ai-lens/responsible-ai-lens.html) — 책임 있는 AI 관점.

**모범 사례**: 6개 기둥 전체 — 운영 우수성 · 보안 · 신뢰성 · 성능 효율성 · 비용 최적화 · 지속 가능성.

---

## 계속 학습하기

- **[AWS Skill Builder](https://skillbuilder.aws)** — 자습형 디지털 과정, 실습(SPL), 시험 준비.
- **[AWS Training and Certification](https://aws.amazon.com/training/)** — 강의식 교육, 자격증.
- **[AWS Workshops](https://workshops.aws)** — 핸즈온 워크숍.

> 이 자료는 AWS T&C 공식 교육 자료가 아닙니다. 강사가 원본 강사용 덱을 AWS 공식 문서로 검증·최신화한 보조 자료이며, 일부 오류가 있을 수 있으므로 시험·실무 적용 전에는 위 출처 링크를 확인하세요.
