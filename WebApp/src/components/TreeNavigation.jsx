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
    items: (series.children || []).map((item) => ({
      type: 'link',
      text: item.title,
      href: `#/module/${item.id}`,
      info: item.isNew ? <Badge color="blue">NEW</Badge> : undefined,
    })),
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
        event.preventDefault();
        onItemSelect(event.detail.href.replace(/^#\/module\//, ''));
      }}
    />
  );
}
