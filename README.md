# Open Wallet AI — Trend Summary

## 프로젝트 개요
이 모듈은 **뉴스,소비자 동향 데이터를 자동 수집하고**,  
**오픈소스 LLM (Kanana)** 기반으로 최신 **지출 트렌드를 요약**하는 기능을 제공합니다.

---

## How to Use

### STEP 1: 의존성 설치
```bash
cd trend_summary
python -m venv .venv
.venv\Scripts\activate      # (Windows)
# source .venv/bin/activate # (macOS/Linux)
pip install -r requirements.txt
```

### STEP 2: 실행
```bash
python trend_summary.py --keywords "소비 트렌드, 물가, 지출 패턴"
```

결과 예시:
```
[Open Wallet · 이번 주 지출 트렌드 요약]
기간: 2025-11-13 ~ 2025-11-20
키워드: 소비 트렌드, 물가, 지출 패턴
■ 주요 포인트
 - 경기 둔화로 인한 외식 지출 감소
 - 온라인 쇼핑 매출 5% 상승
...
```

---

## Branch 전략 & 네이밍 규칙
- `main`: 배포용  
- `develop`: 개발 통합  
- `feature/3-trend-summary`: 트렌드 요약 기능 개발 브랜치  

PR 제목 예시:
```
feat(trend_summary): add Kanana-based open-source trend summary module
```

---

## 폴더 구조
```
trend_summary/
 ├── trend_summary.py        # Kanana 기반 뉴스 요약 파이프라인
 ├── requirements.txt        # 필요 패키지
 └── README.md               # 사용 가이드 (현재 문서)
```

---

## 기술 스택
- **Crawler**: Google News RSS + BeautifulSoup  
- **LLM**: Kanana 1.5 (kakaocorp/kanana-1.5-2.1b-instruct-2505)  
- **Storage**: SQLite  
- **Language**: Python 3.10+  
- **Environment**: Windows / macOS / Linux