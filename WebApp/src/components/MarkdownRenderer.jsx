import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import CodeBlockWrapper from './CodeBlockWrapper';
import AsciiDiagram from './AsciiDiagram';
import './MarkdownRenderer.css';

// ASCII 아트 다이어그램으로 처리할 언어 태그
const ASCII_LANGUAGES = ['ascii', 'asciiart', 'diagram'];

// 텍스트 추출 유틸리티 (heading에서 slug 생성용)
function extractText(children) {
  if (typeof children === 'string') return children;
  if (Array.isArray(children)) return children.map(extractText).join('');
  if (children?.props?.children) return extractText(children.props.children);
  return '';
}

// slug 생성 (유니코드 지원)
function slugify(text) {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\p{L}\p{N}\s-]/gu, '')
    .replace(/[\s]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// 커스텀 렌더링 컴포넌트
const components = {
  h1({ children, node, ...props }) {
    const id = slugify(extractText(children));
    return <h1 id={id} {...props}>{children}</h1>;
  },
  h2({ children, node, ...props }) {
    const id = slugify(extractText(children));
    return <h2 id={id} {...props}>{children}</h2>;
  },
  h3({ children, node, ...props }) {
    const id = slugify(extractText(children));
    return <h3 id={id} {...props}>{children}</h3>;
  },
  h4({ children, node, ...props }) {
    const id = slugify(extractText(children));
    return <h4 id={id} {...props}>{children}</h4>;
  },
  // pre 태그: 블록 코드를 직접 처리 (ASCII 다이어그램 / 일반 코드 블록)
  pre({ children, node, ...props }) {
    // react-markdown v9: <pre> 안에 <code> 노드가 있음
    // children은 React element (code)
    if (React.isValidElement(children) && children.props) {
      const { className, children: codeChildren } = children.props;
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : '';
      const codeString = String(codeChildren).replace(/\n$/, '');

      // ASCII 아트 다이어그램 (구문 강조·행 번호 없이 그대로 표시)
      if (ASCII_LANGUAGES.includes(language)) {
        return <AsciiDiagram code={codeString} />;
      }

      // 일반 코드 블록
      return <CodeBlockWrapper language={language} code={codeString} />;
    }
    return <pre {...props}>{children}</pre>;
  },
  // 인라인 코드 처리
  code({ node, className, children, ...props }) {
    return <code className="inline-code" {...props}>{children}</code>;
  },
  // 링크 처리 (앵커 + 외부 링크)
  a({ href, children, node, ...props }) {
    if (href?.startsWith('#')) {
      const handleClick = (e) => {
        e.preventDefault();
        const targetId = decodeURIComponent(href.slice(1));
        const el = document.getElementById(targetId);
        if (el) {
          window.location.hash = href;
        }
      };
      return <a href={href} onClick={handleClick} {...props}>{children}</a>;
    }
    return <a href={href} target="_blank" rel="noopener noreferrer" {...props}>{children}</a>;
  },
  // 테이블 감싸기 (반응형 스크롤)
  table({ children, node, ...props }) {
    return (
      <div className="table-wrapper">
        <table {...props}>{children}</table>
      </div>
    );
  },
  // blockquote 스타일링
  blockquote({ children, node, ...props }) {
    return <blockquote className="md-blockquote" {...props}>{children}</blockquote>;
  }
};

export default function MarkdownRenderer({ content }) {
  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
