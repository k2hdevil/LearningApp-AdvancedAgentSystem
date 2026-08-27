#!/usr/bin/env python3
"""프롬프트 캐싱 시연 — 시스템 지침 캐시 (모듈 2 · 파트 3).

정적 요소 우선(Static-First) 패턴으로 시스템 지침을 캐시해,
후속 요청에서 캐시가 재사용되는 것을 cacheReadInputTokens/cacheWriteInputTokens로 확인한다.

사전 조건:
  - AWS 자격 증명 구성 (aws configure 또는 환경 변수)
  - Amazon Bedrock 모델 접근 권한
  - pip install boto3

실행:
  python M02-prompt-caching-system-instructions.py
"""

import boto3

# --- 설정 ---
MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
REGION = "us-east-1"

# --- 시스템 지침 (정적 · 캐시 대상) ---
# 최소 토큰(Claude Sonnet 4.5: 1,024개)을 충족해야 캐시가 작동한다.
# 프로덕션에서는 역할·정책·제품 지식 등이 자연스럽게 1,024를 넘지만,
# 데모에서는 반복으로 최소 요건을 충족시킨다.
SYSTEM_PROMPT_TEXT = (
    "You are a professional customer service agent.\n"
    "Role: Provide helpful, accurate responses to customer inquiries.\n"
    "Tone: Friendly and professional at all times.\n"
    "Constraints:\n"
    "- Always verify information before responding\n"
    "- Never make up facts or policies\n"
    "- Escalate to human agent when uncertain\n"
    "- Protect customer PII in all responses\n"
    "\n"
    "Product knowledge:\n"
    "Our company sells electronics including cameras, laptops, and accessories.\n"
    "Return policy: 30 days for most items, 14 days for opened software.\n"
    "Shipping: Free standard shipping on orders over $50.\n"
    "Warranty: 1 year standard, 3 years extended available for purchase.\n"
    "Support hours: Monday-Friday 9AM-6PM, Saturday 10AM-4PM.\n"
    "Payment methods: Credit cards, debit cards, digital wallets accepted.\n"
) * 20  # 반복하여 최소 토큰(1,024) 확실히 충족


def call_with_cache(client, user_question: str, label: str) -> None:
    """시스템 지침을 캐시 체크포인트와 함께 보내고 캐시 토큰 정보를 출력한다."""
    response = client.converse(
        modelId=MODEL_ID,
        # 시스템 지침에 cachePoint 적용 (정적 요소 우선)
        system=[
            {"text": SYSTEM_PROMPT_TEXT},
            {"cachePoint": {"type": "default"}},   # ← 여기까지 캐시
        ],
        messages=[
            {
                "role": "user",
                "content": [{"text": user_question}],  # 동적: 매번 새로 처리
            }
        ],
        inferenceConfig={"maxTokens": 150},
    )

    # 응답 및 캐시 토큰 정보 출력
    answer = response["output"]["message"]["content"][0]["text"]
    usage = response["usage"]

    print(f"[{label}]")
    print(f"  질문: {user_question}")
    print(f"  응답: {answer[:100]}...")
    print()
    print(f"  ─── 토큰 사용량 ───")
    print(f"  inputTokens:           {usage.get('inputTokens', 0):>6}  (캐시 안 된 입력 토큰)")
    print(f"  outputTokens:          {usage.get('outputTokens', 0):>6}")
    print(f"  cacheWriteInputTokens: {usage.get('cacheWriteInputTokens', 0):>6}  ← 캐시에 새로 기록된 토큰")
    print(f"  cacheReadInputTokens:  {usage.get('cacheReadInputTokens', 0):>6}  ← 캐시에서 읽은 토큰 (저비용)")
    print(f"  totalTokens:           {usage.get('totalTokens', 0):>6}")
    if "cacheDetails" in usage:
        for detail in usage["cacheDetails"]:
            print(f"  cacheDetails:          TTL={detail.get('ttl', '?')}, cachedTokens={detail.get('inputTokens', '?')}")
    print()


def main():
    print(f"모델: {MODEL_ID}")
    print(f"리전: {REGION}")
    print(f"{'=' * 60}")
    print()

    client = boto3.client("bedrock-runtime", region_name=REGION)

    # 1번째 호출: 캐시 기록 (cacheWriteInputTokens > 0 기대)
    call_with_cache(client, "What is your return policy for cameras?", "1번째 호출 — 캐시 기록")

    # 2번째 호출: 캐시 읽기 (cacheReadInputTokens > 0 기대)
    call_with_cache(client, "Do you offer free shipping?", "2번째 호출 — 캐시 재사용")

    # 3번째 호출: 캐시 재사용 지속 확인
    call_with_cache(client, "What warranty options are available?", "3번째 호출 — 캐시 재사용 지속")

    print(f"{'=' * 60}")
    print("핵심 포인트:")
    print("  • 1번째: cacheWriteInputTokens > 0 → 시스템 지침이 캐시에 기록됨")
    print("  • 2·3번째: cacheReadInputTokens > 0 → 캐시에서 읽음 (재처리 생략, 저비용)")
    print("  • inputTokens는 캐시되지 않은 부분(사용자 질문)만 과금")
    print("  • 동일 시스템 지침을 쓰는 모든 요청이 TTL(5분/1시간) 내 캐시 공유")
    print("  • 주의: 시스템 지침이 최소 토큰(Claude Sonnet 4.5: 1,024)을 넘어야 캐시 작동")


if __name__ == "__main__":
    main()
