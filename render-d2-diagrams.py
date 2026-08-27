#!/usr/bin/env python3
"""마크다운 파일 안의 ```d2 코드 블록을 SVG로 렌더링하고, 선택적으로 이미지 링크를 삽입합니다.

사용법:
    python3 render-d2-diagrams.py Contents/M01-다중에이전트.md            # 렌더링만
    python3 render-d2-diagrams.py --embed Contents/M01-다중에이전트.md    # 렌더링 + md에 이미지 삽입
    python3 render-d2-diagrams.py --embed Contents/M0*.md                 # 여러 파일 일괄

동작:
    - ```d2 블록을 찾아 <md폴더>/diagrams/<파일stem>-NN.svg 로 렌더링
    - --embed 시 각 D2 블록 바로 뒤에 <img> 태그를 삽입 (D2 소스는 그대로 유지)
    - 다이어그램 방향(가로/세로)에 따라 표시 폭을 자동 제한:
        * 세로형(portrait, 높이>폭): 본문 폭의 약 절반(HALF_W) 이내
        * 가로형(landscape): 본문 폭(FULL_W) 이내
    - 멱등: 이미 삽입된 이미지(<!--d2img--> 마커)는 갱신만 하므로 반복 실행해도 중복되지 않음

전제: d2 CLI 설치 (brew install d2)
편집 워크플로: md의 ```d2 소스를 수정 → 이 스크립트를 --embed로 재실행 → 이미지·크기 자동 갱신
"""
import re
import subprocess
import sys
from pathlib import Path

HALF_W = 360   # 세로로 긴(portrait) 다이어그램 최대 표시 폭 (본문 폭의 약 절반)
FULL_W = 720   # 가로형/정사각 다이어그램 최대 표시 폭 (본문 폭)
PAD = 16       # 다이어그램 주변 여백(px). d2 기본값 100 → 축소

D2_ONLY_RE = re.compile(r"```d2\n(.*?)\n```", re.DOTALL)
# D2 블록 + (선택적) 기존 삽입 이미지(마크다운 ![] 또는 <img>)까지 매칭 → 멱등 재삽입
BLOCK_RE = re.compile(
    r"(```d2\n.*?\n```)"
    r"(?:\n\n<!--d2img-->\n(?:!\[[^\]]*\]\([^)]*\)|<img\b[^>]*>))?",
    re.DOTALL,
)


def svg_size(path: Path):
    """SVG의 내재 폭/높이(px)를 반환. width/height 속성 우선, 없으면 viewBox."""
    head = path.read_text(encoding="utf-8", errors="ignore")[:4000]
    m = re.search(r"<svg\b[^>]*>", head, re.I)
    tag = m.group(0) if m else head
    w = re.search(r'\bwidth="([\d.]+)', tag)
    h = re.search(r'\bheight="([\d.]+)', tag)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    vb = re.search(r'viewBox="\s*[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)', tag)
    if vb:
        return float(vb.group(1)), float(vb.group(2))
    return None, None


def display_width(path: Path) -> int:
    """가로세로 비율에 따라 표시 폭을 결정한다.
    - 뚜렷한 세로형(H > W×1.25): 높이가 과도해지므로 폭을 절반(HALF_W) 이내로 제한
    - 균형/가로형: 본문 폭(FULL_W) 이내에서 가능하면 원본 크기로 표시(글씨 크기 유지)
    """
    w, h = svg_size(path)
    if not w:
        return HALF_W
    if h and h > w * 1.25:
        return min(int(round(w)), HALF_W)
    return min(int(round(w)), FULL_W)


def render_file(md_path: Path, embed: bool = False) -> int:
    text = md_path.read_text(encoding="utf-8")
    codes = D2_ONLY_RE.findall(text)
    if not codes:
        print(f"  (D2 블록 없음) {md_path.name}")
        return 0

    out_dir = md_path.parent / "diagrams"
    out_dir.mkdir(exist_ok=True)
    stem = md_path.stem
    ok = 0

    for i, code in enumerate(codes, 1):
        svg = out_dir / f"{stem}-{i:02d}.svg"
        proc = subprocess.run(
            ["d2", "--pad", str(PAD), "-", str(svg)],
            input=code.encode("utf-8"),
            capture_output=True,
        )
        if proc.returncode == 0:
            ok += 1
        else:
            err = proc.stderr.decode("utf-8", "ignore").strip()[:200]
            print(f"  ERR block #{i}: {err}")

    if embed:
        counter = {"n": 0}

        def repl(m):
            counter["n"] += 1
            n = counter["n"]
            name = f"{stem}-{n:02d}.svg"
            w = display_width(out_dir / name)
            img = f'<img src="diagrams/{name}" alt="diagram {n}" width="{w}">'
            return f"{m.group(1)}\n\n<!--d2img-->\n{img}"

        md_path.write_text(BLOCK_RE.sub(repl, text), encoding="utf-8")
        print(f"  OK  {md_path.name}: {ok}개 렌더링 + <img> 삽입/갱신(크기 자동)")
    else:
        print(f"  OK  {md_path.name}: {ok}개 렌더링 (→ {out_dir.name}/)")
    return ok


def main():
    args = sys.argv[1:]
    embed = "--embed" in args
    files = [Path(a) for a in args if a != "--embed"]
    if not files:
        print("사용법: python3 render-d2-diagrams.py [--embed] <파일.md> ...")
        return
    total = sum(render_file(f, embed=embed) for f in files if f.exists())
    print(f"\n총 {total}개 다이어그램 처리 완료.")


if __name__ == "__main__":
    main()
