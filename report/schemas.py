# 코드 작성일 25/11/21
# 데이터/요청/응답 스키마
# 차후 수정 가능
# schemas.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class Transaction(BaseModel):
    date: Optional[str]
    merchant: Optional[str]
    amount: Optional[int]
    suggested_category: Optional[str] = None


class ReportRequest(BaseModel):
    """
    /api/report 요청용 바디
    - user_id: 분석 대상 사용자 ID
    - start_date, end_date: "YYYY-MM-DD" 문자열 (옵션)
    - question: 기본 리포트 대신 사용자 맞춤 질문을 하고 싶을 때
    """
    user_id: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    question: Optional[str] = None


class ReportResponse(BaseModel):
    """
    /api/report 응답 바디
    """
    report: str
    user_id: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    transaction_count: int
