# main.py
"""
OpenWallet Unified FastAPI Server
 - OCR 영수증 분석
 - 소비 통계/집계 (총액 / Top 가맹점 / 추세)
 - 외부 트렌드 요약 (Kanana)
 - Qwen 기반 개인 소비 리포트
"""
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import time
from sqlalchemy.exc import OperationalError

# 1) 기존 모듈 import
# OCR: ocr/main.py 에 있는 로직 재사용
from ocr.main import (
    OCRResult,
    run_vision_ocr,
    normalize,
    extract_merchant,
    extract_amount,
    extract_date,
    extract_items,
    suggest_category,
)
# 트렌드 요약: trend_summary.py
from trend_summary import run as run_trend_summary, TrendSummary

# Qwen 리포트: report/ 폴더
try:
    from report.qwen_model import generate_spending_report
    QWEN_AVAILABLE = True
except Exception:
    QWEN_AVAILABLE = False
    def generate_spending_report(*args, **kwargs):
        return "(로컬 개발 환경에서는 Qwen 모델을 사용할 수 없습니다.)"
    
from report import models
from report import schemas
from report.database import engine, get_db


MAX_RETRIES = 5
for i in range(MAX_RETRIES):
    try:
        print(f"Database connection attempt {i+1}...")
        models.Base.metadata.create_all(bind=engine)
        print("Database connection successful!")
        break
    except OperationalError as e:
        print(f"Database not ready yet, retrying in 2 seconds... Error: {e}")
        time.sleep(2)
        if i == MAX_RETRIES - 1:
            print("Failed to connect to Database after multiple attempts.")
            raise e

# 2) FastAPI 앱 공통 설정
app = FastAPI(
    title="OpenWallet Unified API",
    version="1.0.0",
    description="OpenWallet OCR + Stats + Trend Summary + AI Report Backend",
)

# 프론트랑 바로 붙일 수 있게 CORS 기본 열어둠
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# OCR 영수증 파서 API

@app.post("/ocr-receipt", response_model=OCRResult)
async def api_ocr_receipt(
    file: UploadFile = File(...),
    memo: Optional[str] = Form(default=None),
):
    """
    이미지 영수증 업로드 → OCR → 가맹점/금액/날짜/품목/카테고리 추출.
    기존 ocr/main.py 로직을 그대로 사용.
    """
    try:
        content = await file.read()

        if len(content) == 0:
            raise HTTPException(400, "빈 파일입니다.")
        if len(content) > 8 * 1024 * 1024:
            raise HTTPException(413, "이미지 크기가 너무 큽니다(>8MB).")

        text = run_vision_ocr(content)
        lines = normalize(text)

        merchant = extract_merchant(lines)
        amount = extract_amount(text)
        date = extract_date(text)
        items = extract_items(lines)
        cat = suggest_category(merchant, items, memo)

        return OCRResult(
            merchant=merchant,
            amount=amount,
            date=date,
            items=items,
            suggested_category=cat,
            raw_text=text,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"OCR 처리 중 오류: {e}")

# 3. 외부 트렌드 요약 API (Kanana + SQLite)

class TrendSummaryRequest(BaseModel):
    keywords: List[str]
    days: int = 7
    max_articles: int = 30
    model: str = "kakaocorp/kanana-1.5-2.1b-instruct-2505"
    db_path: str = "./openwallet_trends.db"


class TrendSummaryResponse(BaseModel):
    period_start: str
    period_end: str
    keywords: List[str]
    bullets: List[str]
    key_stats: List[str]
    risks: List[str]
    opportunities: List[str]
    sources: List[str]
    model: str


@app.post("/trends/summary", response_model=TrendSummaryResponse)
def api_trend_summary(req: TrendSummaryRequest):
    """
    Google News RSS + Kanana로 최근 N일 간의 소비/경제 트렌드 요약.
    trend_summary.run() 사용.
    """
    summary: TrendSummary = run_trend_summary(
        db=req.db_path,
        keywords=req.keywords,
        days=req.days,
        max_articles=req.max_articles,
        model=req.model,
    )

    return TrendSummaryResponse(
        period_start=summary.period_start,
        period_end=summary.period_end,
        keywords=summary.keywords,
        bullets=summary.bullets,
        key_stats=summary.key_stats,
        risks=summary.risks,
        opportunities=summary.opportunities,
        sources=summary.sources,
        model=summary.model,
    )
    
# 4. Qwen 기반 개인 소비 리포트 API
# (기존 report/main.py 로직 그대로)

@app.post("/report", response_model=schemas.ReportResponse)
def create_report(request: schemas.ReportRequest, db: Session = Depends(get_db)):
    # 1. DB 조회: 날짜 범위 필터링
    # 지출 입력 API는 없지만, DB에 이미 저장된 'models.Expense' 데이터를 읽어와야 리포트 작성이 가능합니다.
    expenses_query = db.query(models.Expense).filter(
        models.Expense.date >= request.start_date,
        models.Expense.date <= request.end_date
    )
    expenses = expenses_query.all()

    if not expenses:
        raise HTTPException(
            status_code=404, 
            detail="해당 기간에 조회된 지출 데이터가 없습니다."
        )
    total_amount = 0
    category_summary = {} # 예: {"FOOD": 50000, "TRANSPORT": 30000}
    # 2. 데이터 변환: ORM 객체 -> 딕셔너리 리스트 (모델 입력용)
    # 수정사항 카테고리별 합계 계산
    transaction_list = []
    for exp in expenses:
            # 1. 전체 합계 계산
            total_amount += exp.price
            
            # 2. 카테고리별 합계 계산
            cat_name = exp.category
            if cat_name not in category_summary:
                category_summary[cat_name] = 0
            category_summary[cat_name] += exp.price
            
            # 3. 상세 내역은 개수 제한 (리포트 전달 개수 조절 가능 현재는 30)
            if len(transaction_list) < 30: 
                transaction_list.append({
                    "date": str(exp.date),
                    "merchant": exp.title,
                    "amount": exp.price,
                    "category": exp.category
                })

    # 3. 모델에게 줄 데이터 재구성
    # 상세 내역 대신 요약 정보를 줍니다.
    summary_text = {
        "total_spent": total_amount,
        "category_breakdown": category_summary,
        "recent_transactions_sample": transaction_list # 샘플만 전달
    }

    # 3. 모델 추론: 리포트 생성
    try:
        report_text = generate_spending_report(
            transactions=transaction_list,
            user_question=request.question
        )
    except Exception as e:
        print(f"LLM Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"리포트 생성 중 오류가 발생했습니다: {str(e)}")

    # 4. 결과 반환
    return schemas.ReportResponse(
        report=report_text,
        start_date=request.start_date,
        end_date=request.end_date,
        transaction_count=len(expenses)
    )

# 5. Health Check

@app.get("/health")
def health():
    return {"status": "ok", "service": "OpenWallet Unified API"}
