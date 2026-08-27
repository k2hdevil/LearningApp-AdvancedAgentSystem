#!/usr/bin/env python3
"""
ASCII 아트 다이어그램 정렬 검증 도구

마크다운의 ```ascii 코드 블록을 찾아 박스 테두리가 어긋나는지 검사합니다.

한글은 고정폭 폰트에서 2칸을 차지하므로, 박스 안에 한글 라벨을 넣으면
테두리(│)를 맞추기 위해 공백 개수를 문자 수가 아니라 '표시 폭'으로 계산해야
합니다. 이 스크립트가 그 계산을 대신 검사합니다.

사용법:
    python3 verify-ascii-diagrams.py Contents/M01-MultiAgent.md
    python3 verify-ascii-diagrams.py Contents/*.md
    python3 verify-ascii-diagrams.py --show Contents/M01-MultiAgent.md   # 폭도 함께 출력
"""

import re
import sys
import unicodedata

# 박스 테두리로 쓰는 문자 (고정폭 폰트에서 1칸으로 렌더링됨)
BOX_CHARS = set('─│┌┐└┘├┤┬┴┼━┃╭╮╰╯')
# 세로 테두리를 이루는 문자 (열 정렬 검사 대상)
VERTICAL_CHARS = set('│┌┐└┘├┤┬┴┼┃')
# 세로 흐름의 끝을 표시하는 ASCII 화살촉. 테두리와 같은 열에 놓이므로
# 열 정렬 검사에서 유효한 연결점으로 함께 인정한다.
ARROW_HEADS = set('v^')

# 폭이 폰트에 따라 1칸/2칸으로 달라지는 문자 → 다이어그램 안에서는 쓰지 않는다
AMBIGUOUS_CHARS = {
    '→': '-->', '←': '<--', '↑': '^', '↓': 'v',
    '▶': '>', '◀': '<', '▲': '^', '▼': 'v',
    '►': '>', '◄': '<', '·': '/', '—': '--', '–': '-',
    '■': '#', '□': '#', '●': 'o', '○': 'o', '◆': '*', '★': '*',
    '⇅': '^v', '⇄': '<>', '↔': '<->', '⇆': '<->',
}


def char_width(ch: str) -> int:
    """문자 하나의 표시 폭. 한글/CJK는 2칸, 그 외는 1칸."""
    if ch in BOX_CHARS:
        # 박스 그리기 문자는 Unicode East Asian Width 가 Ambiguous 지만
        # 고정폭 폰트(D2Coding, Noto Sans Mono CJK 등)에서는 1칸이다.
        return 1
    if unicodedata.east_asian_width(ch) in ('W', 'F'):
        return 2
    return 1


def display_width(text: str) -> int:
    """문자열의 표시 폭 합계."""
    return sum(char_width(ch) for ch in text)


def vertical_columns(line: str) -> set:
    """줄에서 세로 테두리 문자가 놓인 표시 열(column) 위치 집합."""
    columns = set()
    col = 0
    for ch in line:
        if ch in VERTICAL_CHARS:
            columns.add(col)
        col += char_width(ch)
    return columns


def connector_columns(line: str) -> set:
    """세로 흐름이 지나가는 모든 열. 테두리 + 화살촉(v, ^)을 포함한다."""
    columns = set()
    col = 0
    for ch in line:
        if ch in VERTICAL_CHARS or ch in ARROW_HEADS:
            columns.add(col)
        col += char_width(ch)
    return columns


def strip_quote(line: str) -> str:
    """blockquote 안의 코드 블록도 검사하려고 앞의 '> ' 인용 표시를 벗겨냅니다.

    마크다운은 '> ' 를 제거한 나머지를 코드 블록 내용으로 다루므로,
    인용 표시를 벗긴 뒤 검사해야 실제 렌더링 결과와 같아집니다.
    """
    stripped = line
    while True:
        match = re.match(r'^\s*>( ?)(.*)$', stripped)
        if not match:
            return stripped
        stripped = match.group(2)


def extract_ascii_blocks(text: str):
    """```ascii ... ``` 블록을 (시작 줄번호, 줄 목록) 형태로 뽑아냅니다.

    blockquote(`> `) 안에 들어 있는 블록도 함께 찾습니다.
    """
    blocks = []
    lines = text.split('\n')
    inside = False
    start = 0
    buffer = []
    for index, raw in enumerate(lines, start=1):
        line = strip_quote(raw)
        if not inside and re.match(r'^```(ascii|asciiart|diagram)\s*$', line.strip()):
            inside = True
            start = index
            buffer = []
            continue
        if inside and line.strip() == '```':
            blocks.append((start, buffer))
            inside = False
            continue
        if inside:
            buffer.append((index, line))
    return blocks


def border_after_wide(line: str):
    """한글(2칸 문자) 뒤에 놓인 테두리 문자를 찾아 반환합니다.

    이것이 정렬이 깨지는 진짜 원인입니다. 한글 뒤에 테두리가 오면
    그 테두리의 위치가 '한글이 정확히 2칸인지'에 달리게 되는데,
    한글 고정폭 폰트가 없는 환경(맥 기본 상태)에서는 한글이 가변폭
    폰트로 대체되므로 2칸이 보장되지 않습니다.

    테두리를 항상 한글보다 왼쪽에만 두면 정렬이 ASCII 문자로만
    결정되어 폰트와 무관하게 안전합니다.
    """
    seen_wide = False
    for ch in line:
        if unicodedata.east_asian_width(ch) in ('W', 'F'):
            seen_wide = True
        elif seen_wide and ch in BOX_CHARS:
            return ch
    return None


def check_block(start_line: int, rows, show: bool):
    """블록 하나를 검사하고 문제 목록을 반환합니다."""
    problems = []

    # 1) 폭이 폰트에 따라 달라지는 문자 사용 여부
    for line_no, line in rows:
        for ch in line:
            if ch in AMBIGUOUS_CHARS:
                problems.append(
                    f'  {line_no}행: 폭이 불안정한 문자 {ch!r} 사용 '
                    f'(권장 대체: {AMBIGUOUS_CHARS[ch]!r})'
                )

    # 2) 한글 뒤의 테두리 문자 — 폰트에 따라 반드시 어긋난다
    for line_no, line in rows:
        found = border_after_wide(line)
        if found:
            problems.append(
                f'  {line_no}행: 한글 뒤에 테두리 문자 {found!r} 가 옵니다. '
                f'한글 폭에 정렬이 의존하므로 폰트에 따라 어긋납니다 '
                f'(테두리는 한글보다 왼쪽에만 두세요)'
            )

    # 3) 세로 테두리 열 정렬 — 다른 줄과 공유되지 않는 고아 열을 찾는다.
    #    분기 코너(┌ ┐)는 아래쪽 화살촉(v)으로 이어지므로 화살촉 열도 함께 센다.
    column_counts = {}
    for _, line in rows:
        for col in connector_columns(line):
            column_counts[col] = column_counts.get(col, 0) + 1

    for line_no, line in rows:
        orphans = sorted(
            col for col in vertical_columns(line) if column_counts.get(col, 0) < 2
        )
        if orphans:
            problems.append(
                f'  {line_no}행: 테두리가 어긋난 열 {orphans} '
                f'(다른 줄과 맞지 않음) | 표시폭 {display_width(line)}'
            )

    if show:
        print(f'  --- 블록 시작 {start_line}행 · 줄별 표시폭 ---')
        for line_no, line in rows:
            print(f'  {line_no:>5} w={display_width(line):>3} |{line}')

    return problems


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    show = '--show' in sys.argv

    if not args:
        print(__doc__)
        return 1

    total_problems = 0
    for path in args:
        try:
            with open(path, encoding='utf-8') as handle:
                text = handle.read()
        except OSError as error:
            print(f'{path}: 읽을 수 없습니다 ({error})')
            total_problems += 1
            continue

        blocks = extract_ascii_blocks(text)
        print(f'\n=== {path} — ascii 블록 {len(blocks)}개 ===')

        for start_line, rows in blocks:
            problems = check_block(start_line, rows, show)
            if problems:
                print(f'  [블록 @{start_line}행] 문제 {len(problems)}건')
                for problem in problems:
                    print(problem)
                total_problems += len(problems)
            else:
                print(f'  [블록 @{start_line}행] 정렬 정상 ({len(rows)}줄)')

    print(f'\n총 문제 {total_problems}건')
    return 1 if total_problems else 0


if __name__ == '__main__':
    sys.exit(main())
