#작성일 : 25/11/30
from sqlalchemy import Column, String, Integer, Date, Text
from database import Base
import uuid

# UUID 생성을 위한 함수
def generate_uuid():
    return str(uuid.uuid4())

class Expense(Base):
    __tablename__ = "expense"

    # UUID를 PK로 사용
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    
    # user_id = Column(String, index=True, nullable=True) 
    title = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    price = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    emotion = Column(String, nullable=False)
    memo = Column(Text, nullable=True)
    satisfaction = Column(Integer, nullable=False)

class Favorite(Base):
    __tablename__ = "favorite"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    
    # user_id = Column(String, index=True, nullable=True)
    title = Column(String, nullable=True)
    price = Column(Integer, nullable=True)
    category = Column(String, nullable=True)