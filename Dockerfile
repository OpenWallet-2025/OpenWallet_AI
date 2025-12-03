# 1. 가볍고 안정적인 Python 슬림 버전 사용 (버전은 프로젝트에 맞춰 변경 가능)
FROM python:3.10.8

# 2. 컨테이너 내부 작업 디렉토리 설정
WORKDIR /app

# 3. 캐싱 효율을 위해 requirements.txt 먼저 복사 및 설치
# (Dockerfile 위치 기준 하위 폴더인 OpenWallet_AI/requirements.txt를 가져옴)
COPY requirements.txt .

# 4. 의존성 설치 (--no-cache-dir로 이미지 크기 최소화)
RUN pip install --no-cache-dir -r requirements.txt

# 5. 나머지 소스 코드 복사
# (OpenWallet_AI 폴더 내부의 모든 파일을 컨테이너의 /app으로 복사)
COPY . .

# 6. 포트 노출 선언 (문서화 목적 및 일부 도구 지원용)
EXPOSE 8000

# 7. FastAPI 실행 (Uvicorn 사용 가정)
# --host 0.0.0.0: 컨테이너 외부에서 접근 가능하게 설정 (필수)
# --port 8081: 쿠버네티스 포트와 일치시킴 (필수)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]