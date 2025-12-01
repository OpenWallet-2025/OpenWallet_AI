from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# 모듈 임포트
import models
import schemas
from database import engine, get_db
from qwen_model import generate_spending_report

# DB 테이블 생성 (앱 시작 시 자동 생성 - 읽기 전용이라도 테이블 정의는 필요)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="OpenWallet Report Service", version="0.1.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# 리포트 (Report) API
# =========================================================

@app.post("/api/report", response_model=schemas.ReportResponse)
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

    # 2. 데이터 변환: ORM 객체 -> 딕셔너리 리스트 (모델 입력용)
    transaction_list = []
    for exp in expenses:
        transaction_list.append({
            "date": str(exp.date),
            "merchant": exp.title,
            "amount": exp.price,
            "category": exp.category,
            "emotion": exp.emotion,
            "memo": exp.memo
        })

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
        transaction_count=len(transaction_list)
    )