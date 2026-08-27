import React, { useState, useEffect, useCallback } from 'react';
import TopNavigation from '@cloudscape-design/components/top-navigation';
import AppLayout from '@cloudscape-design/components/app-layout';
import BreadcrumbGroup from '@cloudscape-design/components/breadcrumb-group';
import { DarkModeProvider, useDarkMode } from './contexts/DarkModeContext';
import { DEFAULT_MODULE_ID, moduleTitle } from './data/navigationTree';
import TreeNavigation from './components/TreeNavigation';
import MarkdownRenderer from './components/MarkdownRenderer';
import { moonIcon, sunIcon } from './components/ThemeIcons';

// 기본 모듈 ID
const DEFAULT_MODULE = DEFAULT_MODULE_ID;

function AppContent() {
  const { darkMode, toggleDarkMode } = useDarkMode();
  const [navOpen, setNavOpen] = useState(true);
  const [activeModule, setActiveModule] = useState(() => {
    // URL 해시에서 모듈 ID 파싱
    const hash = window.location.hash.replace('#', '');
    if (hash && hash.startsWith('/module/')) {
      return hash.replace('/module/', '');
    }
    return DEFAULT_MODULE;
  });
  const [markdownContent, setMarkdownContent] = useState('');
  const [loading, setLoading] = useState(true);

  // 마크다운 콘텐츠 로드
  const loadContent = useCallback(async (moduleId) => {
    setLoading(true);
    try {
      const response = await fetch(`/content/${moduleId}.md`);
      if (response.ok) {
        const text = await response.text();
        setMarkdownContent(text);
      } else {
        setMarkdownContent(`# 콘텐츠를 찾을 수 없습니다\n\n요청한 모듈(${moduleId})을 로드할 수 없습니다.`);
      }
    } catch (error) {
      setMarkdownContent(`# 오류 발생\n\n콘텐츠를 로드하는 중 오류가 발생했습니다: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadContent(activeModule);
  }, [activeModule, loadContent]);

  // 해시 변경 감지
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (hash && hash.startsWith('/module/')) {
        setActiveModule(hash.replace('/module/', ''));
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // 사이드바 항목 선택 핸들러
  const handleItemSelect = (moduleId) => {
    window.location.hash = `/module/${moduleId}`;
    setActiveModule(moduleId);
    // 콘텐츠 영역 맨 위로 스크롤
    window.scrollTo(0, 0);
  };

  // 브레드크럼 항목 생성
  const breadcrumbItems = [
    { text: 'Home', href: '#/' },
    { text: moduleTitle(activeModule), href: `#/module/${activeModule}` }
  ];

  return (
    <>
      <div id="top-nav">
        <TopNavigation
          identity={{
            href: '#/',
            title: 'Agentic AI Training Series',
            logo: {
              src: '/images/agentic-ai-logo.svg',
              alt: 'Agentic AI Training Series 로고'
            }
          }}
          utilities={[
            {
              // 텍스트 없이 아이콘만 표시한다. 누르면 반대 모드로 전환되므로
              // 현재 모드가 아니라 '전환될 모드'의 아이콘을 보여준다.
              type: 'button',
              iconSvg: darkMode ? sunIcon : moonIcon,
              ariaLabel: darkMode ? '라이트 모드로 전환' : '다크 모드로 전환',
              onClick: toggleDarkMode,
              // 좁은 화면에서 오버플로 메뉴로 접히면 아이콘만으로는 의미가 사라진다
              disableUtilityCollapse: true
            }
          ]}
        />
      </div>
      <AppLayout
        headerSelector="#top-nav"
        navigationOpen={navOpen}
        onNavigationChange={({ detail }) => setNavOpen(detail.open)}
        toolsHide={true}
        navigationWidth={280}
        breadcrumbs={
          <BreadcrumbGroup
            items={breadcrumbItems}
            onFollow={(event) => {
              event.preventDefault();
              if (event.detail.href === '#/') {
                window.location.hash = `/module/${DEFAULT_MODULE}`;
                setActiveModule(DEFAULT_MODULE);
              }
            }}
          />
        }
        navigation={
          <TreeNavigation
            activeItemId={activeModule}
            onItemSelect={handleItemSelect}
          />
        }
        content={
          <div className="content-area">
            {loading ? (
              <div className="loading-container">로딩 중...</div>
            ) : (
              <MarkdownRenderer content={markdownContent} />
            )}
          </div>
        }
        ariaLabels={{
          navigation: '사이드 네비게이션',
          navigationClose: '네비게이션 닫기',
          navigationToggle: '네비게이션 열기'
        }}
      />
    </>
  );
}

export default function App() {
  return (
    <DarkModeProvider>
      <AppContent />
    </DarkModeProvider>
  );
}
