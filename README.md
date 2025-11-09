# 🌿 Open Wallet AI Branch 전략 & 네이밍 규칙

Open Wallet AI 팀은 **AI 소비 분석 및 지출 인사이트 제공 서비스**를 개발합니다.  
효율적인 협업과 안정적인 배포를 위해 다음과 같은 **Git Branch 전략**을 적용합니다.

---

## 🔹 Branch 종류

| Branch | 역할 | 설명 |
|---------|------|------|
| **main** | 배포용 브랜치 | 실제 서비스에 배포 가능한 **안정 버전**만 존재합니다. 개발자는 직접 커밋하지 않습니다. |
| **develop** | 개발 통합 브랜치 | 각 기능(feature) 브랜치를 병합하고 테스트하는 **개발용 통합 브랜치**입니다. |
| **feature** | 기능 개발 브랜치 | 새로운 기능을 개발할 때 **develop**에서 분기하여 작업 후 develop에 병합합니다. |
| **release** | 배포 준비 브랜치 | 배포 전 테스트, 문서 정리, 버그 수정 등을 진행하며 **새로운 기능 추가는 금지**됩니다. |
| **hotfix** | 긴급 수정 브랜치 | 배포 후 발생한 버그를 긴급히 수정할 때 main에서 분기 후 main, develop에 병합합니다. |

---

## 🧩 네이밍 규칙

| 종류 | 예시 | 규칙 |
|------|------|------|
| **main / develop** | `main`, `develop` | 그대로 사용 |
| **feature** | `feature/5-ocr-receipt-parser`, `feature/14-emotion-analysis`, `feature/22-ai-report-generator` | `feature/{issue-number}-{feature-name}` 형식 |
| **release** | `release-1.2.0`, `release-2025Q1` | `release-{version}` 또는 `release-{기간}` |
| **hotfix** | `hotfix-1.2.1` | `hotfix-{version}` 형식 |

---

## 💡 Tip for New Members

- 항상 **develop 브랜치에서 작업을 시작**하세요.  
- **절대 main 브랜치에 직접 커밋하지 마세요.**  
- 브랜치 이름만 봐도 어떤 작업인지 한눈에 알 수 있도록 작성하세요.  
- 기능 단위로 브랜치를 작게 나누면 코드 리뷰와 충돌 해결이 쉬워집니다.  

---

## 🧠 AI 기능별 브랜치 예시

| 기능 | 브랜치명 예시 | 설명 |
|------|---------------|------|
| **OCR 기반 자동 입력** | `feature/5-ocr-receipt-parser` | Google Vision OCR을 이용한 영수증 자동 인식 기능 |
| **자동 카테고리 분류** | `feature/8-category-predictor` | 인식된 상호명·품목 키워드 기반 카테고리 분류 모델 |
| **감정 기반 소비 분석** | `feature/14-emotion-analysis` | 감정 태그와 소비 패턴 상관관계 분석 AI |
| **메모 기반 피드백** | `feature/17-context-feedback` | 자연어 메모 분석을 통한 개인 맞춤형 피드백 |
| **AI 소비 리포트** | `feature/22-ai-report-generator` | 주간/월간 소비 리포트를 자동 생성하는 GPT 분석기 |
| **소비 코치 챗봇** | `feature/31-chat-coach` | 대화형 소비 습관 코치 AI (예: “이번 주 낭비한 건 뭐야?”) |
| **지출 트렌드 뉴스 크롤러** | `feature/40-expense-trend-crawler` | Web Crawling 기반 소비 트렌드 분석 모듈 |
| **소셜/챌린지 기능** | `feature/44-social-challenge` | 커피 챌린지, 배지, 순위 기능 구현 |
| **정기 결제 알림** | `feature/48-subscription-alert` | 구독 결제 3일 전 알림 서비스 |

---

## 📘 예시 워크플로우

```bash
# 1️⃣ develop 브랜치에서 새 브랜치 생성
git checkout develop
git pull origin develop
git checkout -b feature/14-emotion-analysis

# 2️⃣ 기능 개발 후 커밋
git add .
git commit -m "feat: add emotion-based spending analysis model"

# 3️⃣ 원격 저장소로 푸시
git push origin feature/14-emotion-analysis

# 4️⃣ Pull Request 생성 → 코드 리뷰 후 develop으로 병합
```

---

## 🪴 Branch 병합 흐름

```
feature → develop → release → main
          ↑                 ↓
        hotfix ──────────────┘
```

---

## 🧾 Commit Convention

| 타입 | 의미 | 예시 |
|------|------|------|
| **feat:** | 새로운 기능 추가 | `feat: add OCR receipt parsing with Google Vision` |
| **fix:** | 버그 수정 | `fix: resolve null error in category predictor` |
| **docs:** | 문서 수정 | `docs: update README with branch rules` |
| **refactor:** | 코드 구조 변경 | `refactor: optimize emotion model pipeline` |
| **test:** | 테스트 코드 추가 | `test: add OCR parser unit tests` |
| **chore:** | 기타 작업 (환경 설정 등) | `chore: update dependencies` |

---

## 🧩 PR 템플릿

```markdown
## 🧠 작업 개요
- [ ] 새로운 기능 추가
- [ ] 버그 수정
- [ ] 리팩터링
- [ ] 문서 / 설정 변경

## ✨ 변경 내용
- 구현한 기능: (예시) 감정 기반 소비 분석 모델
- 주요 변경 파일: `ai/modules/emotion_analysis.py`
- 테스트 완료 여부: ✅

## 🧩 이슈 번호
Closes #14
```

---

## 🌱 협업 기본 규칙

- 모든 PR은 **최소 1명 이상의 리뷰 승인** 후 병합합니다.  
- **release → main 병합** 시 배포 진행 및 버전 태그 추가 (`v1.0.0`).  
- 병합된 feature 브랜치는 **반드시 삭제** (`git branch -d feature/...`).  
- 민감 정보(`.env`, API 키, DB 설정 등)는 `.gitignore`로 제외합니다.  

---