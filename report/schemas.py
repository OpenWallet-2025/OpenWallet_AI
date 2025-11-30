#작성일 : 25/11/30
from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum
from datetime import date as date_type

# 명세서 정의
class CategoryEnum(str, Enum):
    FOOD = "FOOD"             # 식비
    LIVING = "LIVING"         # 생활
    TRANSPORT = "TRANSPORT"   # 교통비
    HEALTH = "HEALTH"         # 의료, 건강
    CULTURE = "CULTURE"       # 취미, 문화생활
    EDUCATION = "EDUCATION"   # 교육, 자기계발
    CLOTHING = "CLOTHING"     # 의류
    ETC = "ETC"               # 기타

class EmotionEnum(str, Enum):
    HAPPY = "HAPPY"           # 기분 좋은 상태
    EXCITED = "EXCITED"       # 들뜸
    SAD = "SAD"               # 우울
    ANGRY = "ANGRY"           # 화남
    STRESSED = "STRESSED"     # 스트레스
    NEUTRAL = "NEUTRAL"       # 무감정

# Expense Schemas
class ExpenseBase(BaseModel):
    title: str
    date: date_type
    price: int = Field(..., gt=0, description="Price must be greater than 0")
    category: CategoryEnum
    emotion: EmotionEnum
    memo: Optional[str] = None
    satisfaction: int = Field(..., ge=1, le=5, description="Satisfaction must be 1~5")

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[date_type] = None
    price: Optional[int] = Field(None, gt=0)
    category: Optional[CategoryEnum] = None
    emotion: Optional[EmotionEnum] = None
    memo: Optional[str] = None
    satisfaction: Optional[int] = Field(None, ge=1, le=5)

class ExpenseResponse(ExpenseBase):
    id: str

    class Config:
        from_attributes = True # ORM 모드 활성화 (구 orm_mode)

# --- Favorite Schemas ---
class FavoriteBase(BaseModel):
    title: Optional[str] = None
    price: Optional[int] = None
    category: Optional[CategoryEnum] = None

class FavoriteCreate(FavoriteBase):
    pass

class FavoriteUpdate(FavoriteBase):
    # 수정 시 미입력 항목은 null(None)로 수정된다는 명세 반영
    title: Optional[str] = None
    price: Optional[int] = None
    category: Optional[CategoryEnum] = None

class FavoriteResponse(FavoriteBase):
    id: str

    class Config:
        from_attributes = True