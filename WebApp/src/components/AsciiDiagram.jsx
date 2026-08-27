import React from 'react';
import './AsciiDiagram.css';

/**
 * ASCII 아트 다이어그램 렌더러
 *
 * ```ascii 코드 블록을 구문 강조 없이 그대로 표시합니다.
 * 외부 네트워크에 의존하지 않고, 다크 모드에서도 Cloudscape 토큰을 따라
 * 색이 반전됩니다.
 *
 * 한글은 모노스페이스 폰트에서 2칸을 차지하므로, 박스 테두리가 어긋나지
 * 않도록 CSS에서 CJK 고정폭 폰트를 우선 지정합니다(AsciiDiagram.css 참조).
 */
export default function AsciiDiagram({ code }) {
  return (
    <figure className="ascii-diagram">
      <pre className="ascii-diagram-body">{code}</pre>
    </figure>
  );
}
