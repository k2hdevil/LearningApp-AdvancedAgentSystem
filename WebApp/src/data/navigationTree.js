/**
 * 계층적 내비게이션 트리 데이터 구조
 * 시리즈(최상위) > 개별 모듈(하위) 2단계 계층
 *
 * 모듈 번호는 콘텐츠 문서의 H1 제목과 1:1로 맞춥니다.
 * 수강생이 사이드바와 본문을 대조하기 때문입니다.
 *
 * isNew: true 인 항목은 사이드바에 NEW 배지가 표시됩니다.
 */

/** 최초 진입 시 표시할 모듈 */
export const DEFAULT_MODULE_ID = 'M00-CourseIntro';

/** @type {Array<{id: string, title: string, type: string, children?: Array}>} */
export const NAVIGATION_TREE = [
  {
    id: 'series-advanced-agentic-systems',
    title: 'Building Advanced Agentic Systems on AWS',
    type: 'series',
    children: [
      {
        id: 'M00-CourseIntro',
        title: '모듈 0: 과정 개요 및 소개',
        type: 'item',
      },
      {
        id: 'M01-MultiAgent',
        title: '모듈 1: 다중 에이전트 아키텍처 및 통신 패턴',
        type: 'item',
      },
      {
        id: 'M02-ContextEngineering',
        title: '모듈 2: 컨텍스트 엔지니어링 및 성능 최적화',
        type: 'item',
      },
      {
        id: 'M03-Security',
        title: '모듈 3: 보안 및 규정 준수 구현',
        type: 'item',
      },
      {
        id: 'M04-Observability',
        title: '모듈 4: 프로덕션 모니터링, 관찰성 및 평가',
        type: 'item',
      },
      {
        id: 'M05-WellArchitected',
        title: '모듈 5: Well-Architected 에이전틱 AI 시스템',
        type: 'item',
      },
      {
        id: 'M06-WrapUp',
        title: '모듈 6: 참고 자료 및 공식 문서',
        type: 'item',
      },
    ],
  },
];

/**
 * 트리에서 ID로 노드를 검색한다. 재귀적으로 모든 자식 노드를 탐색한다.
 * @param {Array} tree - 내비게이션 트리 배열
 * @param {string} id - 검색할 노드 ID
 * @returns {Object|null} 찾은 노드 또는 null
 */
export function findNodeById(tree, id) {
  for (const node of tree) {
    if (node.id === id) return node;
    if (node.children) {
      const found = findNodeById(node.children, id);
      if (found) return found;
    }
  }
  return null;
}

/**
 * 모듈 ID에 해당하는 표시 제목을 반환한다. 브레드크럼 등에 사용한다.
 * @param {string} id - 모듈 ID
 * @returns {string} 표시 제목 (없으면 ID 그대로)
 */
export function moduleTitle(id) {
  return findNodeById(NAVIGATION_TREE, id)?.title ?? id;
}
