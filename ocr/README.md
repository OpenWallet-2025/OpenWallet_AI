# Open Wallet AI — OCR

## Branch 전략 & 네이밍 규칙

Open Wallet AI 팀은 AI 소비 분석 및 지출 인사이트 제공 서비스를 개발합니다.
효율적인 협업과 안정적인 배포를 위해 다음과 같은 Git Branch 전략을 적용합니다.

| Branch      | 역할        | 설명                                               |
| ----------- | --------- | ------------------------------------------------ |
| **main**    | 배포용 브랜치   | 실제 서비스에 배포 가능한 안정 버전만 존재합니다. 개발자는 직접 커미트하지 않습니다. |
| **develop** | 개발 통합 브랜치 | 기능(feature) 브랜치를 병합하고 테스트하는 개발용 통합 브랜치입니다.       |
| **feature** | 기능 개발 브랜치 | 새로운 기능 개발 시 develop에서 분기하여 작업 후 develop에 병합합니다.  |
| **release** | 배포 준비 브랜치 | 배포 전 테스트, 문서 정리, 버그 수정용으로 사용됩니다.                 |
| **hotfix**  | 긴급 수정 브랜치 | 배포 후 발생한 버그를 main에서 수정 후 main, develop에 반영합니다.   |

🔹 **브랜치 네이밍 규칙**

* `main`, `develop` → 그대로 사용
* `feature/{기능명}` 예: `feature/1-ocr-receipt-parser`
* `release/{버전}` 예: `release/1.2.0`
* `hotfix/{버전}` 예: `hotfix/1.2.1`

---

## 프로젝트 개요

이 모듈은 Google Cloud Vision OCR을 이용해
영수증 이미지를 자동으로 인식하고, 금액·상호명·날짜·품목을 추출하여
지출 내역 입력을 자동화하는 기능을 제공합니다.

---

## How to Use

### STEP 1 : 가상환경 생성 및 의존성 설치

```bash
cd ai/ocr
python -m venv .venv
.venv\Scripts\activate      # (Windows)
# source .venv/bin/activate # (macOS/Linux)
pip install -r requirements.txt
```

### STEP 2 : 서버 실행

```bash
python main.py
```

실행 후 브라우저에서
🔗 [http://localhost:8000/docs](http://localhost:8000/docs)
→ `/api/ocr-receipt` 엔드포인트에서 이미지 업로드 테스트 가능

---

## Git 작업 가이드

### 1. develop에서 기능 브랜치 생성

```bash
git checkout develop
git pull origin develop
git checkout -b feature/1-ocr-receipt-parser
```

### 2. 에커푸

```bash
git add .
git commit -m "feat(ocr): add OCR receipt parsing using Google Vision"
git push origin feature/1-ocr-receipt-parser
```

### 3. Pull Request 생성

GitHub에서 `develop` 브랜치를 대상으로
`feature/1-ocr-receipt-parser`를 병합하는 PR 생성 후 리뷰/승인 진행.

PR 제목 예시:

```text
feat(ocr): add OCR receipt parsing using Google Vision
```

PR 본문:

```text
Closes #1
```

---

## 📂 폴더 구조

```
ai/
└── ocr/
    ├── main.py              # FastAPI 서버 (OCR 처리 및 카테고리 추출)
    ├── requirements.txt     # 필요한 패키지 목록
    └── README.md            # (현재 문서)
```

---

## 기술 스택

* **Backend:** FastAPI
* **OCR Engine:** Google Cloud Vision API
* **Language:** Python 3.10+
* **Environment:** Windows / macOS / Linux