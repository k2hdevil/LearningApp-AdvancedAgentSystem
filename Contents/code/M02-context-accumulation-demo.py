#!/usr/bin/env python3
"""컨텍스트 누적 시연 (모듈 2 · 파트 1).

에이전트 루프에서 messages 배열에 메시지가 쌓이며 토큰이 실시간으로
누적되는 모습을 보여준다. 한 번의 사용자 문의가 여러 메시지
(user -> assistant -> tool_use -> tool_result)를 추가하고,
토큰은 줄지 않고 '커지기만 한다'는 점을 눈으로 확인할 수 있다.

실행:        python M02-context-accumulation-demo.py
정확도 향상:  pip install tiktoken   (없으면 근사치로 동작)
"""

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


def main() -> None:
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


if __name__ == "__main__":
    main()
