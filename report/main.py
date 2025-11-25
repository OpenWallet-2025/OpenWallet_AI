# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import ReportRequest, ReportResponse
from db import get_transactions_from_db
from qwen_model import generate_spending_report

app = FastAPI(title="OpenWallet Report API", version="0.1.0")

# 필요 시 CORS 허용 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 서비스에서는 도메인 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/report", response_model=ReportResponse)
def create_report(request: ReportRequest):
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
    report = generate_spending_report(
        transactions=transactions,
        user_question=request.question,
    )

    # 3) 응답 구성
    return ReportResponse(
        report=report,
        user_id=request.user_id,
        start_date=request.start_date,
        end_date=request.end_date,
        transaction_count=len(transactions),
    )
