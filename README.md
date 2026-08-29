# Building Advanced Agentic Systems on AWS — 학습 웹앱

AWS의 고급 에이전틱 시스템 구축 과정(300레벨 심화, 한국어)을 위한 학습 자료와 이를 제공하는 웹 애플리케이션입니다. 강의 콘텐츠(모듈 0~6)와 실습 노트북(Jupyter)을 Cloudscape 기반 단일 페이지 앱으로 열람할 수 있습니다.

> 이 자료는 AWS 공식 교육 자료가 아닙니다. 원본 강사용 덱을 AWS 공식 문서로 검증·재구성한 보조 학습 자료이며, 오류가 있을 수 있으므로 시험·실무 적용 전에는 각 모듈의 참고 문서(모듈 6)를 확인하세요.

---

## 콘텐츠 구성

| 모듈 | 주제 |
| --- | --- |
| 모듈 0 | 과정 개요 및 소개 |
| 모듈 1 | 다중 에이전트 아키텍처 및 통신 패턴 |
| 모듈 2 | 컨텍스트 엔지니어링 및 성능 최적화 |
| 모듈 3 | 보안 및 규정 준수 구현 |
| 모듈 4 | 프로덕션 모니터링, 관찰성 및 평가 |
| 모듈 5 | Well-Architected 에이전틱 AI 시스템 |
| 모듈 6 | 참고 자료 및 공식 문서 |

**실습 노트북** (사이드바에서 다운로드)

- 실습 1.1 — Strands Agents를 통한 개인 예산 도우미 구축
- 실습 1.2 — Strands를 사용하여 다중 에이전트 워크플로 구축
- 실습 1.3 — Amazon Bedrock AgentCore에 에이전트 배포

각 노트북의 코드 셀에는 수강생이 스스로 코드 리뷰를 할 수 있도록 한국어 학습 주석(API 호출·반복문·파싱·데이터 흐름)이 달려 있습니다.

---

## 기술 스택

- **React 18** + **Vite 5** — SPA 프런트엔드, 해시 기반 라우팅
- **Cloudscape Design System** — AWS 콘솔 스타일 UI 컴포넌트, 다크/라이트 모드
- **react-markdown** (+ remark-gfm, rehype-raw) — 마크다운 콘텐츠 렌더링
- **react-syntax-highlighter** — 코드 블록 구문 강조
- 다이어그램은 외부 렌더링 없이 **ASCII 아트**로 표현(네트워크 의존 없음, 다크 모드 대응)

---

## 프로젝트 구조

```
.
├── amplify.yml                  # AWS Amplify 빌드 설정 (appRoot: WebApp)
├── Contents/                    # 원본 학습 콘텐츠 (저작용 원본)
│   ├── M00-CourseIntro.md ~ M06-WrapUp.md
│   ├── L01-Task-1~3_ko_kr.ipynb # 실습 노트북
│   ├── diagrams/                # (레거시) 원본 D2 다이어그램 SVG — 현재 미사용
│   └── _slide-transcript-backup/# 원본 슬라이드 전사본
├── WebApp/                      # 배포 대상 웹 애플리케이션
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   │   ├── content/             # 앱이 실제로 읽는 마크다운 (Contents 에서 동기화)
│   │   ├── notebooks/           # 다운로드용 실습 노트북
│   │   └── images/              # 로고 등 정적 이미지
│   └── src/
│       ├── App.jsx              # AppLayout + TopNavigation
│       ├── components/          # MarkdownRenderer, AsciiDiagram, TreeNavigation 등
│       ├── contexts/            # DarkModeContext
│       └── data/navigationTree.js  # 사이드바 네비게이션 정의
├── render-d2-diagrams.py        # (로컬 저작 도구) D2 -> SVG 렌더링
└── verify-ascii-diagrams.py     # (로컬 저작 도구) ASCII 다이어그램 정렬 검증
```

> `Contents/`는 콘텐츠 **원본**이고, 앱이 실제 서빙하는 것은 `WebApp/public/content/`입니다. 콘텐츠를 수정하면 두 위치를 동기화해야 합니다(아래 참조).

---

## 로컬 개발

사전 요구: Node.js 18 이상

```bash
cd WebApp
npm install
npm run dev        # http://localhost:3000 에서 실행 (자동으로 브라우저 열림)
```

프로덕션 빌드 미리보기:

```bash
npm run build      # WebApp/dist 생성
npm run preview
```

### 콘텐츠 수정 시

앱은 `WebApp/public/content/`의 마크다운을 읽습니다. `Contents/`의 원본을 수정했다면 해당 파일을 복사해 동기화하세요.

```bash
# 예: 모듈 3 수정 후 동기화
cp Contents/M03-Security.md WebApp/public/content/M03-Security.md
```

### 다이어그램 정렬 검증 (선택)

ASCII 다이어그램은 한글이 고정폭 폰트에서 2칸을 차지해 정렬이 깨지기 쉽습니다. 아래 도구로 검증할 수 있습니다.

```bash
python3 verify-ascii-diagrams.py Contents/M01-MultiAgent.md
```

---

## 배포 (AWS Amplify Hosting — GitHub 연동)

이 프로젝트는 **GitHub 리포지토리에 푸시하면 AWS Amplify가 자동으로 빌드·배포**하는 방식을 사용합니다.

### 빌드 설정 (`amplify.yml`)

리포지토리 루트의 `amplify.yml`을 Amplify가 자동으로 읽습니다. 프런트엔드가 루트가 아니라 `WebApp/` 아래에 있으므로 `appRoot: WebApp`으로 지정되어 있습니다.

```yaml
version: 1
applications:
  - appRoot: WebApp
    frontend:
      phases:
        preBuild:
          commands:
            - npm ci
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: dist
        files:
          - '**/*'
      cache:
        paths:
          - node_modules/**/*
```

### 최초 연결 (한 번만)

1. **AWS Amplify 콘솔** → "Deploy an app" → **GitHub** 선택
2. 리포지토리 `k2hdevil/LearningApp-AdvancedAgentSystem`, 브랜치 `main` 선택
   (최초 연결 시 Amplify GitHub App 설치 권한 승인 필요)
3. Amplify가 `amplify.yml`을 자동 감지 — `appRoot: WebApp`, `baseDirectory: dist` 확인
4. **SPA 리다이렉트 규칙 추가** (앱 설정 → Rewrites and redirects)

   AWS가 단일 페이지 앱(SPA)에 권장하는 규칙은, 정적 자산(css·js·png 등)을 제외한 모든 요청을
   `/index.html`로 **200 재작성(Rewrite)**하는 것입니다. 콘솔의 JSON 편집기에 아래를 넣습니다.

   ```json
   [
     {
       "source": "</^[^.]+$|\\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json|webp)$)([^.]+$)/>",
       "target": "/index.html",
       "status": "200",
       "condition": null
     }
   ]
   ```

   이 앱은 해시 라우팅(`#/module/...`)이라 새로고침 404가 잘 나지 않지만, 정적 자산 경로 보호와
   직접 URL 접근 안정성을 위해 설정을 권장합니다.
   (참고: [Amplify — SPA 리다이렉트](https://docs.aws.amazon.com/amplify/latest/userguide/redirect-rewrite-examples.html))

### 이후 배포

`main` 브랜치에 푸시하면 Amplify가 자동으로 빌드·배포합니다.

```bash
git add -A
git commit -m "docs: update module 3 content"
git push origin main   # -> Amplify 자동 빌드 트리거
```

배포 진행 상황과 로그는 Amplify 콘솔에서 확인합니다.

---

## 라이선스 및 고지

학습·교육 목적의 자료입니다. 코드 예제의 계정 ID·리소스 이름 등은 예시 값이며, 실제 실습은 별도 실습 환경에서 진행하는 것을 전제로 합니다.
