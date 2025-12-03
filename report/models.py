# 작성일 : 25/11/30
from sqlalchemy import Column, String, Integer, Date, Text
from database import Base
import uuid

# UUID 생성을 위한 함수
def generate_uuid():
    return str(uuid.uuid4())

class Expense(Base):
    __tablename__ = "expense"

    #user_id 생략
    # UUID는 36자이므로 String(36)으로 지정
    expense_id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    
    # [수정] 일반 문자열은 넉넉하게 255자로 지정합니다.
    title = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    price = Column(Integer, nullable=False)
    
    # 카테고리나 감정은 길이가 짧으므로 50~255 사이로 지정
    category = Column(String(50), nullable=False)
    emotion = Column(String(50), nullable=False)
    
    # Text 타입은 길이가 필요 없습니다 (긴 글 저장용)
    memo = Column(Text, nullable=True)
    satisfaction = Column(Integer, nullable=False)

# 리포트 기능만 쓰더라도 DB 테이블 정의는 필요할 수 있어 남겨두거나, 
# 아예 안 쓴다면 삭제해도 됩니다. (여기서는 에러 방지용으로 길이만 수정)
class Favorite(Base):
    __tablename__ = "favorite"

    favorate_id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    
    title = Column(String(255), nullable=True)
    price = Column(Integer, nullable=True)
    category = Column(String(50), nullable=True)