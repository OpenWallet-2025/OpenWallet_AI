from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

# 모듈 임포트
import models
import schemas
from database import engine, get_db

# DB 테이블 생성 (앱 시작 시 자동 생성)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="OpenWallet API", version="0.1.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# 지출 (Expenses) API
# ---------------------------------------------------------

@app.post("/api/expenses", response_model=List[schemas.ExpenseResponse], status_code=status.HTTP_201_CREATED)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    """
    지출 내역을 저장합니다.
    명세서에 따라 리스트 형태로 반환합니다.
    """
    
    # user_id = request.user_id 
    
    new_expense = models.Expense(
        title=expense.title,
        date=expense.date,
        price=expense.price,
        category=expense.category,
        emotion=expense.emotion,
        memo=expense.memo,
        satisfaction=expense.satisfaction
        # user_id=user_id
    )
    
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    
    return [new_expense]

@app.get("/api/expenses", response_model=List[schemas.ExpenseResponse])
def get_expenses(db: Session = Depends(get_db)):
    """
    저장한 모든 지출 내역을 불러옵니다.
    """
    # user_id 필터링 제거 (모든 데이터 조회)
    expenses = db.query(models.Expense).all()
    return expenses

@app.patch("/api/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
def update_expense(expense_id: str, expense_update: schemas.ExpenseUpdate, db: Session = Depends(get_db)):
    """
    해당 id의 지출 내역을 수정합니다.
    """
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    
    if not db_expense:
        # 명세서: 없는 {id} 요청 시 500 Error (일반적으로는 404지만 명세 준수 시 500 고려)
        # 하지만 통상적인 API 설계를 위해 404를 기본으로 하되, 500이 강제라면 raise HTTPException(status_code=500) 사용
        raise HTTPException(status_code=500, detail="Expense not found")

    # 입력된 값만 업데이트 (exclude_unset=True)
    update_data = expense_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_expense, key, value)
    
    db.commit()
    db.refresh(db_expense)
    
    return db_expense

@app.delete("/api/expenses/{expense_id}", status_code=status.HTTP_200_OK)
def delete_expense(expense_id: str, db: Session = Depends(get_db)):
    """
    해당 id의 지출 내역을 삭제합니다.
    """
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    
    if not db_expense:
        # 명세서: 없는 ID 요청 시 500
        raise HTTPException(status_code=500, detail="Expense not found")
    
    db.delete(db_expense)
    db.commit()
    return {"detail": "Successfully deleted"}

# ---------------------------------------------------------
# 즐겨찾기 (Favorites) API
# ---------------------------------------------------------

@app.post("/api/favorite", response_model=schemas.FavoriteResponse, status_code=status.HTTP_201_CREATED)
def create_favorite(favorite: schemas.FavoriteCreate, db: Session = Depends(get_db)):
    """
    자주 사용하는 지출 항목을 저장합니다.
    """
    new_favorite = models.Favorite(
        title=favorite.title,
        price=favorite.price,
        category=favorite.category
        # user_id=...
    )
    
    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)
    
    return new_favorite

@app.get("/api/favorite", response_model=List[schemas.FavoriteResponse])
def get_favorites(db: Session = Depends(get_db)):
    """
    즐겨찾기된 내역을 모두 불러옵니다.
    """
    favorites = db.query(models.Favorite).all()
    return favorites

@app.patch("/api/favorite/{favorite_id}", response_model=schemas.FavoriteResponse)
def update_favorite(favorite_id: str, favorite_update: schemas.FavoriteUpdate, db: Session = Depends(get_db)):
    """
    즐겨찾기 내역을 수정합니다.
    * 수정 시 미입력한 항목은 null로 수정됨 (명세서 특이사항 반영)
    """
    db_favorite = db.query(models.Favorite).filter(models.Favorite.id == favorite_id).first()
    
    if not db_favorite:
        raise HTTPException(status_code=500, detail="Favorite not found")

    # 명세서 특이사항: "미입력한 항목시 null로 수정됨"
    # 따라서 exclude_unset=True를 쓰지 않고, 명시적으로 들어온 값(None 포함)을 그대로 덮어씁니다.
    db_favorite.title = favorite_update.title
    db_favorite.price = favorite_update.price
    db_favorite.category = favorite_update.category
    
    db.commit()
    db.refresh(db_favorite)
    
    return db_favorite

@app.delete("/api/favorite/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_favorite(favorite_id: str, db: Session = Depends(get_db)):
    """
    해당 즐겨찾기 내역을 삭제합니다. 성공 시 204.
    """
    db_favorite = db.query(models.Favorite).filter(models.Favorite.id == favorite_id).first()
    
    if not db_favorite:
        # 204 No Content 반환 시에는 Body가 없으므로 
        # 없는 ID라도 멱등성을 위해 그냥 성공 처리하거나 에러를 낼 수 있음.
        # 여기서는 로직 흐름상 에러 처리
        raise HTTPException(status_code=500, detail="Favorite not found")
        
    db.delete(db_favorite)
    db.commit()
    return