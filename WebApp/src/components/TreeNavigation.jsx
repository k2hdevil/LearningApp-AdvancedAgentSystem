import Badge from '@cloudscape-design/components/badge';
import SideNavigation from '@cloudscape-design/components/side-navigation';
import { NAVIGATION_TREE } from '../data/navigationTree';

/**
 * navigationTree 데이터를 Cloudscape SideNavigation items 형식으로 변환한다.
 * - series  -> section (접을 수 있는 그룹, 기본 확장)
 * - 개별 모듈 -> link (href 에 모듈 ID 를 해시로 사용)
 * - isNew   -> info 슬롯에 NEW 배지
 *
 * @param {Array} navigationTree - 계층적 내비게이션 트리
 * @returns {Array} SideNavigation items 배열
 */
export function toSideNavigationItems(navigationTree) {
  return navigationTree.map((series) => ({
    type: 'section',
    text: series.title,
    items: (series.children || []).map((item) => {
      // download 타입(실습): 콘텐츠 전환이 아니라 .ipynb 파일을 내려받는 링크.
      if (item.type === 'download') {
        return {
          type: 'link',
          text: item.title,
          href: `/notebooks/${item.downloadFile}`,  // public/notebooks/ 아래 정적 파일
          external: true,                            // onFollow 에서 다운로드로 분기하는 표식
          info: <Badge color="green">노트북</Badge>,
        };
      }
      // 일반 모듈: 해시 라우팅으로 본문을 전환한다.
      return {
        type: 'link',
        text: item.title,
        href: `#/module/${item.id}`,
        info: item.isNew ? <Badge color="blue">NEW</Badge> : undefined,
      };
    }),
  }));
}

/**
 * TreeNavigation - Cloudscape SideNavigation 기반 모듈 내비게이션
 *
 * 라우터가 없으므로 href 에 `#/module/<id>` 해시를 사용하고,
 * onFollow 에서 기본 이동을 막은 뒤 onItemSelect 콜백으로 활성 모듈을 전환한다.
 * 접근성·키보드 탐색·활성 항목 표시는 SideNavigation 이 기본 제공한다.
 *
 * @param {Object} props
 * @param {string} props.activeItemId - 현재 활성 모듈 ID
 * @param {function} props.onItemSelect - 항목 선택 콜백 (모듈 ID 전달)
 */
export default function TreeNavigation({ activeItemId, onItemSelect }) {
  const items = toSideNavigationItems(NAVIGATION_TREE);

  return (
    <SideNavigation
      activeHref={`#/module/${activeItemId}`}
      items={items}
      onFollow={(event) => {
        const href = event.detail.href;
        // 실습 다운로드 링크(/notebooks/*.ipynb): 새 탭에 JSON 원문이 열리는 대신
        // 클릭 즉시 파일로 저장되도록, 임시 <a download> 앵커를 만들어 클릭한다.
        if (event.detail.external && href.startsWith('/notebooks/')) {
          event.preventDefault();
          const a = document.createElement('a');
          a.href = href;
          a.download = href.split('/').pop();  // 저장 파일명 = .ipynb 파일명
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          return;
        }
        // 모듈 링크는 SPA 내 전환이므로 기본 이동을 막고 활성 모듈만 바꾼다.
        event.preventDefault();
        onItemSelect(href.replace(/^#\/module\//, ''));
      }}
    />
  );
}
