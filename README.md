# Open Wallet AI – Unified API Server
> 2025년 11월 25일 업데이트

Open Wallet AI는 영수증 OCR, 소비 분석, 트렌드 요약, LLM 기반 개인 소비 리포트 생성 기능을 제공하는 **통합 FastAPI 서버**입니다.

본 저장소는 AI 기능을 모듈로 구성하고, 모든 기능을 하나의 서버에서 사용할 수 있도록 통합한 버전을 포함하고 있습니다.

---

# 주요 기능

### 1. OCR 영수증 분석  
Google Vision OCR 기반으로 영수증에서 다음 정보를 자동 추출:
- 가맹점명
- 결제금액
- 결제일자
- 품목 리스트
- 카테고리 추천

---

### 2. 소비 통계 분석  
내부 DB의 거래기록을 기반으로:
- 총 지출액  
- Top 가맹점  
- 일별 지출 추세  

등을 계산하여 반환합니다.

---

### 3. 외부 소비 트렌드 요약  
외부 소비 분석 API를 호출하여  
**요약된 트렌드 텍스트**를 제공합니다.

---

### 4. 개인 소비 분석 리포트
사용자의 전체 소비 패턴을 기반으로  
Qwen 모델이 **요약 리포트**를 생성합니다.

---

# How to Use

## 1. 설치

```bash
git clone https://github.com/OpenWallet-2025/OpenWallet_AI.git
cd OpenWallet_AI
pip install -r requirements.txt
```

---

## 2. FastAPI 서버 실행

```bash
uvicorn main:app --reload
```

### Swagger UI  
http://127.0.0.1:8000/docs

### ReDoc  
http://127.0.0.1:8000/redoc

---

# API 명세서

## Health Check  
`GET /health`

```json
{ "status": "ok" }
```

---

## OCR – 영수증 분석  
`POST /api/ocr-receipt`

Request (multipart/form-data):

| 필드 | 설명 |
|-----|------|
| file | 영수증 이미지 |

Response Example:

```json
{
  "merchant": "스타벅스",
  "amount": 5800,
  "date": "2025-11-24",
  "items": [{ "name": "콜드브루", "price": 4800 }],
  "category": "카페/음료",
  "raw_text": "..."
}
```

---

## 소비 통계 API

### 총 지출액  
`GET /api/spend/total`

### Top 가맹점  
`GET /api/spend/top-merchants`

### 소비 추세  
`GET /api/spend/trend`

---

## 소비 트렌드 요약  
`GET /api/trend-summary`

---

## 개인 소비 리포트 (LLM)  
`POST /api/report`

```json
{
  "user_id": "user123",
  "start_date": "2025-11-01",
  "end_date": "2025-11-25"
}
```

---

# Branch 전략 (Git Flow)

본 프로젝트는 Git Flow 전략을 따릅니다.

| Branch | 역할 | 설명 |
|--------|------|------|
| **main** | 배포용 | 실제 서비스 배포 가능한 안정 버전. 직접 커밋 금지 |
| **develop** | 개발 통합 | feature 브랜치가 모두 머지되는 통합 개발 브랜치 |
| **feature/** | 기능 개발 | develop에서 분기 → 기능 개발 → 다시 develop에 머지 |
| **release/** | 배포 준비 | 배포 전 QA, 문서 정리, 테스트. 기능 추가 금지 |
| **hotfix/** | 긴급 수정 | 배포 후 발견된 버그 수정용. main에서 분기 후 main+develop 둘 다 머지 |

---

# 이번 브랜치 정보

현재 브랜치:  
```
feature/5-ai-unified-api-server
```

내용:
- OCR + 소비 통계 + 트렌드 요약 + LLM 리포트 기능 통합
- FastAPI 기반 서버 구축
- curl 및 Swagger 테스트 완료
- API 명세서 업데이트

---

# 프로젝트 구조

```
OpenWallet_AI/
│
├── ocr/                 # OCR 관련 로직
├── report/              # LLM 소비 리포트
├── main.py              # FastAPI 통합 서버
├── tool.py              # 소비 통계 유틸
├── trend_summary.py     # 트렌드 요약 기능
├── requirements.txt
└── README.md
```
