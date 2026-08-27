#!/usr/bin/env python3
"""입력 형식 최적화 시연 (모듈 2 · 파트 2-①).

동일한 에이전트 세션 컨텍스트 데이터를 Pretty JSON과 TOON 형식으로 인코딩해
실제 Amazon Bedrock API(converse)를 호출하여 inputTokens를 비교한다.

사전 조건:
  - AWS 자격 증명 구성 (aws configure 또는 환경 변수)
  - Amazon Bedrock 모델 접근 권한 (기본: us.anthropic.claude-sonnet-4-5-20250929-v1:0)
  - pip install boto3

실행:
  python M02-toon-token-comparison.py
"""

import json
import boto3

# --- 설정 ---
MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"  # 사용할 Bedrock 모델
REGION = "us-east-1"                                        # Bedrock 리전


# ============================================================
# 동일한 데이터를 두 형식으로 인코딩
# ============================================================

# --- (A) Pretty JSON ---
data = {
    "context": {
        "task": "customer_support_session",
        "session_id": "sess_20250315_abc123",
        "timestamp": "2025-03-15T14:30:00Z",
    },
    "agents": ["billing_agent", "technical_agent", "shipping_agent"],
    "conversations": [
        {
            "id": 1,
            "role": "user",
            "content": "I need help with my order 45678",
            "agent": "billing_agent",
            "timestamp": "2025-03-15T14:31:00Z",
            "requiresResponse": True,
        }
    ],
}
pretty_json_str = json.dumps(data, indent=2, ensure_ascii=False)

# --- (B) TOON (Token-Oriented Object Notation) ---
toon_str = """\
context:
  task: customer_support_session
  session_id: sess_20250315_abc123
  timestamp: "2025-03-15T14:30:00Z"
agents[3]: billing_agent,technical_agent,shipping_agent
conversations[1]{id,role,content,agent,timestamp,requiresResponse}:
  1,user,I need help with my order 45678,billing_agent,"2025-03-15T14:31:00Z",true"""


# ============================================================
# Bedrock converse API로 실제 inputTokens 측정
# ============================================================

def measure_input_tokens(client, text: str) -> int:
    """텍스트를 user 메시지로 보내고 응답의 inputTokens를 반환한다."""
    response = client.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": text}],
            }
        ],
        inferenceConfig={
            "maxTokens": 1,  # 응답은 최소로(측정 목적이므로 출력 토큰 낭비 방지)
        },
    )
    return response["usage"]["inputTokens"]


def main():
    print(f"모델: {MODEL_ID}")
    print(f"리전: {REGION}")
    print(f"{'=' * 55}")
    print()

    # Bedrock Runtime 클라이언트 생성
    client = boto3.client("bedrock-runtime", region_name=REGION)

    # Pretty JSON 측정
    print("(A) Pretty JSON 측정 중...")
    json_tokens = measure_input_tokens(client, pretty_json_str)
    print(f"    입력 토큰: {json_tokens}개 | 문자: {len(pretty_json_str)}자")
    print()

    # TOON 측정
    print("(B) TOON 측정 중...")
    toon_tokens = measure_input_tokens(client, toon_str)
    print(f"    입력 토큰: {toon_tokens}개 | 문자: {len(toon_str)}자")
    print()

    # 절감률 계산
    token_saved = (1 - toon_tokens / json_tokens) * 100
    char_saved = (1 - len(toon_str) / len(pretty_json_str)) * 100

    print(f"{'=' * 55}")
    print(f"  토큰 절감: {token_saved:+.1f}% ({json_tokens} → {toon_tokens}, -{json_tokens - toon_tokens}개)")
    print(f"  문자 절감: {char_saved:+.1f}% ({len(pretty_json_str)} → {len(toon_str)}, -{len(pretty_json_str) - len(toon_str)}자)")
    print()
    print("핵심: 동일한 정보인데 형식만 바꿔도 입력 토큰이 줄어든다.")
    print("      반복 전송되는 파이프라인일수록 누적 절감이 커진다.")


if __name__ == "__main__":
    main()
