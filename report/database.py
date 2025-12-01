#작성일 : 25/11/30
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 로컬 Proxy 포트번호에 맞춰서.
USER = "openwallet"
PASSWORD = "openwallet1234"
HOST = "127.0.0.1"
PORT = "3306"   
DB_NAME = "openwallet-db"

# MySQL 연결 URL (pymysql 드라이버 사용)
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

# 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# DB 세션 의존성 주입 (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()