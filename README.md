# 🤖 OpenWallet_AI

> **AI가 당신의 소비를 해석합니다.**  
OpenWallet_AI는 소비 데이터를 기반으로  
**OCR → 감정 분석 → 트렌드 요약 → AI 소비 리포트 생성**  
까지 수행하는 OpenWallet의 핵심 AI 엔진입니다.

---

## Key Features

| 기능 | 설명 |
|------|-----|
| 📸 영수증 OCR 분석 | 금액/가게명/날짜/항목 추출 및 카테고리 추천 |
| 😊 감정 기반 소비 분석 | 감정/만족도 기반 소비 성향 진단 |
| 📈 소비 유형 & 달력 분석 | 패턴 인사이트 + 구독일 자동 추적 |
| 📰 소비 트렌드 뉴스 | 최신 트렌드 뉴스 수집 + 요약 |
| 🤖 AI 소비 리포트 | 사용자 맞춤 소비 성향 분석 + 행동 제안 |

---

## Screenshots

### 📊 Dashboard – 소비 시각화  
![Dashboard Screenshot](./screenshots/dashboard.png)

### 😊 감정 소비 카드  
![Emotion Spending Screenshot](./screenshots/emotion_card.png)

### 📰 소비 트렌드 뉴스  
![Trend](./screenshots/trend.png)

### 🤖 AI 소비 리포트 챗봇  
![AI Report Screenshot](./screenshots/ai_report.png)

### 📈 소비 유형 분석 & 소비 달력  
![AI Analytics](./screenshots/ai_analytics.png)

---

## Architecture
```
[Frontend App]
↓ REST API
[Backend Gateway (Spring)]
↓
[OpenWallet AI Server - FastAPI]
├ OCR (Google Vision)
├ Emotion + Pattern Analysis
├ Trend News Summarizer (Kanana)
└ LLM Consumption Report (Qwen)

✔ 실시간 분석 & 자동화된 AI 파이프라인  
✔ 앱 → 백엔드 → AI 서버 완전 연동
```
---

## Deployment

| 구성 요소 | 기술 |
|------|------|
| Server | FastAPI |
| Cloud | Google Kubernetes Engine |
| CI/CD | GitHub Actions + ArgoCD |
| LLM | Qwen & Kanana |
| Registry | GitHub Container Registry |

---

## Development

```bash
git clone https://github.com/OpenWallet-2025/OpenWallet_AI.git
cd OpenWallet_AI
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## ✨ Vision
- 단순 기록이 아닌, 나를 이해하는 소비 분석 AI
- 소비 습관을 더 건강하게 변화시키는 인공지능
