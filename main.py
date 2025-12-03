# main.py
"""
OpenWallet Unified FastAPI Server
 - OCR 영수증 분석
 - 소비 통계/집계 (총액 / Top 가맹점 / 추세)
 - 외부 트렌드 요약 (Kanana)
 - Qwen 기반 개인 소비 리포트
"""

from typing import List, Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
from report.schemas import ReportRequest, ReportResponse
from report.db import get_transactions_from_db
try:
    from report.qwen_model import generate_spending_report
    QWEN_AVAILABLE = True
except Exception:
    QWEN_AVAILABLE = False
    def generate_spending_report(*args, **kwargs):
        return "(로컬 개발 환경에서는 Qwen 모델을 사용할 수 없습니다.)"


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

@app.post("/report", response_model=ReportResponse)
def api_report(request: ReportRequest):
    """
    - Request: ReportRequest (user_id, start_date, end_date, question)
    - DB에서 거래 내역 조회 후 Qwen으로 리포트 생성
    """
    # 1) DB에서 거래 내역 가져오기
    transactions = get_transactions_from_db(
        user_id=request.user_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )

    if not transactions:
        raise HTTPException(
            status_code=404,
            detail="해당 조건에 해당하는 거래 내역이 없습니다.",
        )

    # 2) Qwen 모델로 리포트 생성
    if not QWEN_AVAILABLE:
        return ReportResponse(
            report="(로컬 개발 환경: Qwen 모델 비활성화됨)",
            user_id=request.user_id,
            start_date=request.start_date,
            end_date=request.end_date,
            transaction_count=len(transactions),
            )

    report_text = generate_spending_report(
        transactions=transactions,
        user_question=request.question,
        )


    # 3) 응답 구성
    return ReportResponse(
        report=report_text,
        user_id=request.user_id,
        start_date=request.start_date,
        end_date=request.end_date,
        transaction_count=len(transactions),
    )

# 5. Health Check

@app.get("/health")
def health():
    return {"status": "ok", "service": "OpenWallet Unified API"}
