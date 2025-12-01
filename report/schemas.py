from pydantic import BaseModel
from datetime import date as date_type

# --- Report Schemas ---
class ReportRequest(BaseModel):
    # 로그인 미구현이므로 user_id 제외
    start_date: date_type
    end_date: date_type
    question: str

class ReportResponse(BaseModel):
    report: str
    start_date: date_type
    end_date: date_type
    transaction_count: int