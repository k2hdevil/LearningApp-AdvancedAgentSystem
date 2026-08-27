/*
 * 상단 내비게이션의 다크/라이트 모드 전환 아이콘.
 *
 * Cloudscape 는 iconSvg 로 넘긴 SVG 에 자체 CSS 를 겁니다.
 *   .awsui_icon > svg    { fill: none }
 *   .awsui_icon > svg *  { stroke: currentColor }
 * 그래서 fill/stroke 를 속성(attribute)으로만 주면 stroke 가 currentColor 로
 * 덮여 원하지 않는 윤곽선이 생깁니다. 위 규칙에 !important 가 없으므로
 * 색을 지정할 도형에는 인라인 style 을 씁니다. 인라인 style 이 항상 이깁니다.
 *
 * 색 선택 기준: Cloudscape TopNavigation 은 라이트 모드에서도 배경이
 * 어둡습니다(#161D26). 두 아이콘 모두 항상 어두운 배경 위에 놓이므로
 * 밝은 색이어야 보입니다.
 */

// 라이트 모드에서 보이는 달 (누르면 다크 모드로 전환)
const MOON_BODY = { fill: '#FFD95E', stroke: 'none' };
const MOON_STAR = { fill: '#9EC5FF', stroke: 'none' };

// 다크 모드에서 보이는 해 (누르면 라이트 모드로 전환)
const SUN_CORE = { fill: '#FFC21F', stroke: 'none' };
const SUN_RAY = { fill: '#FF8A00', stroke: 'none' };

/**
 * 초승달.
 *
 * SVG mask(큰 원에서 작은 원 빼기)는 렌더러에 따라 합성되지 않는 경우가 있어
 * 호(arc) 두 개를 이은 단일 path 로 그립니다.
 *   바깥 호: 중심 (8, 8.2) r=6.3 의 큰 호를 왼쪽으로 돌아갑니다 (large-arc=1, sweep=0).
 *   안쪽 호: 같은 두 점을 r=7.5 로 되돌아옵니다 (sweep=1). 중심이 오른쪽에 놓여
 *            왼쪽으로 볼록해지므로 안쪽이 파여 초승달이 됩니다.
 * 가장 얇은 지점도 약 7px 이라 16px 크기에서 뭉개지지 않습니다.
 */
export const moonIcon = (
  <svg viewBox="0 0 16 16" focusable="false" aria-hidden="true">
    <path
      style={MOON_BODY}
      d="M11.34 2.86A6.3 6.3 0 1 0 11.34 13.54A7.5 7.5 0 0 1 11.34 2.86Z"
    />
    {/* 초승달의 오목한 쪽(오른쪽)에 별 두 개로 색 포인트를 줍니다. */}
    <circle cx="13.1" cy="4.5" r="1.95" style={MOON_STAR} />
    <circle cx="12.7" cy="9.4" r="1.2" style={MOON_STAR} />
  </svg>
);

/**
 * 태양. 중심 원과 8방향 광선을 다른 색으로 칠합니다.
 *
 * 광선은 rect 로 그리고 대각선 4개는 그룹을 45도 회전시켜 만듭니다.
 * 손으로 좌표를 계산한 path 보다 두께를 조절하기 쉽습니다.
 * Cloudscape 가 `svg *` 에 stroke 를 걸기 때문에 도형마다 인라인 style 이 필요합니다.
 */
const sunRays = [0, 45].flatMap((angle) => {
  const rects = [
    { x: 7, y: 0.2, width: 2, height: 3.3 },
    { x: 7, y: 12.5, width: 2, height: 3.3 },
    { x: 0.2, y: 7, width: 3.3, height: 2 },
    { x: 12.5, y: 7, width: 3.3, height: 2 },
  ];
  return rects.map((rect, index) => (
    <rect
      key={`${angle}-${index}`}
      {...rect}
      rx="1"
      style={SUN_RAY}
      transform={angle ? `rotate(${angle} 8 8)` : undefined}
    />
  ));
});

export const sunIcon = (
  <svg viewBox="0 0 16 16" focusable="false" aria-hidden="true">
    {sunRays}
    <circle cx="8" cy="8" r="3.6" style={SUN_CORE} />
  </svg>
);
