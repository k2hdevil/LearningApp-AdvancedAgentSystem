import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vs, vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useDarkMode } from '../contexts/DarkModeContext';

// 복사 버튼을 표시할 언어 목록 (Python만)
const COPYABLE_LANGUAGES = ['python', 'py'];

/*
 * 고정폭 폰트 — Cloudscape 디자인 시스템 표준 스택.
 * 토큰 --font-family-monospace-q47m7k 의 값과 동일하다.
 *
 * 이걸 명시하는 이유: vs 테마는 Consolas 우선, vscDarkPlus 테마는 Menlo 우선으로
 * 서로 다른 스택을 박아 넣는다. macOS 에는 Consolas 가 없어서 라이트 모드는
 * Courier New 로, 다크 모드는 Menlo 로 떨어져 두 모드의 폰트가 달라 보인다.
 * 두 모드 모두 Cloudscape 표준 스택으로 통일한다.
 */
const MONOSPACE =
  'Monaco, Menlo, Consolas, "Courier Prime", Courier, "Courier New", monospace';

/*
 * 코드 본문 배경. 테마가 각각 backgroundColor(vs: white) / background(vscDarkPlus: #1e1e1e)
 * 로 지정하므로, 단축 속성 순서에 기대지 않고 backgroundColor 로 명시적으로 덮어쓴다.
 * 라이트 값은 인라인 코드·ASCII 다이어그램의 라이트 배경(#f3f3f7)과 톤을 맞춘 것이다.
 */
const BACKGROUND = { light: '#f3f3f7', dark: '#1e1e1e' };

// 행 번호는 본문보다 약하게 보여야 한다 (vs 테마는 행 번호 색을 정의하지 않는다)
const LINE_NUMBER_COLOR = { light: '#8c959f', dark: '#6e7681' };

/*
 * 언어 간 색상 일관성 보정.
 *
 * Prism 의 markdown 문법은 `# 제목` 을 `token title important` 로 내보낸다.
 * vscDarkPlus 는 important 에 keyword 와 같은 파랑(#569cd6)을 주지만,
 * vs 는 팔레트에 없는 주황(#e90)을 준다. 그래서 라이트 모드에서만 마크다운 블록이
 * 파이썬 블록과 전혀 다른 색으로 보인다.
 *
 * 두 테마 모두 important 를 keyword 색으로 맞춰, 언어가 달라도 같은 역할이면
 * 같은 색으로 보이게 한다.
 */
function withConsistentPalette(theme) {
  const keywordColor = theme.keyword?.color;
  if (!keywordColor || theme.important?.color === keywordColor) return theme;
  return { ...theme, important: { ...theme.important, color: keywordColor } };
}

const THEME = {
  light: withConsistentPalette(vs),
  dark: withConsistentPalette(vscDarkPlus),
};

export default function CodeBlockWrapper({ language, code }) {
  const { darkMode } = useDarkMode();
  const [copied, setCopied] = useState(false);
  const showCopy = COPYABLE_LANGUAGES.includes(language?.toLowerCase());
  const mode = darkMode ? 'dark' : 'light';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      const textArea = document.createElement('textarea');
      textArea.value = code;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className={`code-block-wrapper is-${mode}`}>
      <div className="code-block-header">
        <span className="code-language">{language || 'text'}</span>
        {showCopy && (
          <button className="copy-button" onClick={handleCopy} aria-label="코드 복사">
            {copied ? '복사됨!' : '복사'}
          </button>
        )}
      </div>
      <SyntaxHighlighter
        language={language || 'text'}
        style={THEME[mode]}
        customStyle={{
          margin: 0,
          // vs 테마가 pre 에 border: 1px solid #dddddd 를 넣어 래퍼 테두리와 겹친다
          border: 'none',
          borderRadius: '0 0 8px 8px',
          fontSize: '13px',
          lineHeight: '1.5',
          fontFamily: MONOSPACE,
          backgroundColor: BACKGROUND[mode],
        }}
        // 폰트는 pre 와 code 양쪽에 지정되므로 code 쪽도 덮어써야 한다
        codeTagProps={{ style: { fontFamily: MONOSPACE, backgroundColor: 'transparent' } }}
        showLineNumbers={code.split('\n').length > 3}
        lineNumberStyle={{ color: LINE_NUMBER_COLOR[mode] }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}
