# version 0.1.1
# 코드 작성일: 2025년 11월 11일
# ocr 1st draft for OpenWallet (merchant 로직 개선)

import io
import os
import re
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# env 변수 로드
load_dotenv()

# Google Vision
USE_VISION = True
try:
    from google.cloud import vision
    vision_client = vision.ImageAnnotatorClient()
except Exception:
    USE_VISION = False
    vision_client = None

app = FastAPI(title="OpenWallet OCR API", version="0.1.1")

# 카테고리 키워드를 통해 분류합니다. 해당 부분은 카테고리를 정한 후 수정할 예정입니다.
CATEGORY_KEYWORDS = {
    "식비": [
        "식당", "분식", "치킨", "고기", "라면", "한식", "중식", "일식", "양식",
        "버거", "피자", "도시락", "뷔페", "김밥", "국밥", "반찬", "포장마차"
    ],
    "카페": [
        "카페", "커피", "스타벅스", "투썸", "폴바셋", "메가커피", "빽다방",
        "디저트", "음료", "베이커리", "빵집"
    ],
    "교통": ["버스", "지하철", "택시", "KTX", "기차", "코레일", "카카오T"],
    "생활": ["다이소", "올리브영", "편의점", "생활", "문구", "세제", "화장지", "주방"],
    "의류": ["유니클로", "지오다노", "스파오", "ZARA", "H&M", "무신사", "의류", "패션"],
    "문화": ["영화", "CGV", "롯데시네마", "메가박스", "도서", "교보문고", "YES24", "공연", "전시"],
    "의료/건강": ["약국", "병원", "치과", "의원", "피트니스", "헬스", "필라테스"],
    "기타": []
}

CURRENCY_SYMBOLS = ["₩", "원", "KRW"]

# Pydantic
class OCRResult(BaseModel):
    merchant: Optional[str] = None
    amount: Optional[int] = None
    date: Optional[str] = None
    items: List[Dict[str, Any]] = []
    suggested_category: Optional[str] = None
    raw_text: Optional[str] = None

# 한글 영수증 전처리/파싱
DATE_PATTERNS = [
    r"(\d{4})[.\-/년\s](\d{1,2})[.\-/월\s](\d{1,2})",      # 2025.11.11 / 2025-11-11 / 2025년 11월 11
    r"(\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})",             # 25/11/11, 25.11.11
    r"(\d{1,2})월\s?(\d{1,2})일"                           # 11월 11일
]

MONEY_PATTERNS = [
    r"(합계|총액|결제금액|결제 금액|총\s*합계|TOTAL)[:\s]*([\d,]+)\s*(?:원|₩)?",
    r"([\d,]+\s*(?:원|₩))",
]

ITEM_LINE_PATTERN = re.compile(
    r"^(.+?)\s+(\d+) ?(개|EA|pcs|PCS)?\s+([\d,]+)[원₩]?$", re.IGNORECASE
)

# 3:29, 3시29, 3:29 1 같은 시간/상단바 라인 감지용
TIME_LINE_RE = re.compile(r"^\s*\d{1,2}[:시]\d{1,2}")

IGNORE_MERCHANT_TOKENS = [
    "영수증", "고객용", "매장용", "부가세", "면세", "신용카드", "현금영수증",
    "결제", "합계", "사업자번호"
]

# 브랜드 힌트: 있으면 이 줄을 최우선으로 상호로 선택
BRAND_HINTS = [
    "스타벅스", "STARBUCKS",
    "맥도날드", "McDonald's",
    "버거킹", "BurgER KING",
    "투썸", "TWOSOME",
    "폴바셋", "PAUL BASSETT",
    "메가커피", "MEGA COFFEE",
]

def normalize(text: str) -> List[str]:
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    return [ln for ln in lines if ln]

def extract_date(text: str) -> Optional[str]:
    for pat in DATE_PATTERNS:
        m = re.search(pat, text)
        if not m:
            continue
        try:
            if len(m.groups()) == 3:
                y, mth, d = m.groups()
                # 2자리 연도 보정
                if len(y) == 2:
                    y = f"20{y}"
                return f"{int(y):04d}-{int(mth):02d}-{int(d):02d}"
            elif len(m.groups()) == 2:  # 11월 11일 패턴은 연도 미포함
                mth, d = m.groups()
                return f"{mth.zfill(2)}-{d.zfill(2)}"  # 연도 미상
        except Exception:
            pass
    return None

def to_int_money(s: str) -> Optional[int]:
    s = s.replace(",", "").replace(" ", "").replace("원", "").replace("₩", "")
    return int(s) if s.isdigit() else None

def extract_amount(text: str) -> Optional[int]:
    # 우선 합계/총액 키워드 우선
    for pat in MONEY_PATTERNS:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            money_str = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)
            val = to_int_money(money_str)
            if val and val > 0:
                return val
    return None

def is_probably_merchant(line: str) -> bool:
    line = line.strip()
    if not line:
        return False

    # 시간 / 상단 상태바 같은 줄은 제외 (예: "3:29 1")
    if TIME_LINE_RE.match(line):
        return False

    # "전자영수증", "결제" 같은 키워드가 들어가면 제외
    if any(tok in line for tok in IGNORE_MERCHANT_TOKENS):
        return False

    # 숫자/기호만 있으면 제외 (:,.-() 등 포함)
    if re.fullmatch(r"[0-9\s.:,\-\(\)]+", line):
        return False

    # 너무 짧은 건 제외 (한글/영문/숫자만 보고 길이 체크)
    core = re.sub(r"[^가-힣A-Za-z0-9]", "", line)
    return len(core) >= 2

def extract_merchant(lines: List[str]) -> Optional[str]:
    # 상단부를 우선 스캔
    top = lines[:10] if len(lines) >= 10 else lines

    # 1) 브랜드 힌트가 있는 줄을 최우선 상호로 사용
    for ln in top:
        if any(h.lower() in ln.lower() for h in BRAND_HINTS):
            return ln

    # 2) 일반적인 상호 후보 검색
    for ln in top:
        if is_probably_merchant(ln):
            return ln

    # 3) 실패 시 하단에서도 탐색
    bottom = lines[-10:] if len(lines) >= 10 else lines
    for ln in bottom:
        if is_probably_merchant(ln):
            return ln
    return None

def extract_items(lines: List[str]) -> List[Dict[str, Any]]:
    items = []
    for ln in lines:
        m = ITEM_LINE_PATTERN.match(ln)
        if m:
            name, qty, _, price = m.groups()
            items.append({
                "name": name.strip(),
                "qty": int(qty),
                "price": to_int_money(price)
            })
    return items

def suggest_category(merchant: Optional[str], items: List[Dict[str, Any]],
                     memo: Optional[str] = None) -> Optional[str]:
    text = " ".join(filter(None, [
        merchant or "",
        " ".join(i["name"] for i in items if i.get("name")),
        memo or ""
    ]))
    score = {cat: 0 for cat in CATEGORY_KEYWORDS.keys()}
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw and kw.lower() in text.lower():
                score[cat] += 1
    # 최고 점수 카테고리
    best = sorted(score.items(), key=lambda x: x[1], reverse=True)
    if best and best[0][1] > 0:
        return best[0][0]
    return None

# OCR
def run_vision_ocr(content_bytes: bytes) -> str:
    if not USE_VISION or not vision_client:
        raise RuntimeError("Google Vision 클라이언트가 준비되지 않았습니다.")
    image = vision.Image(content=content_bytes)
    resp = vision_client.document_text_detection(image=image)
    if resp.error and resp.error.message:
        raise RuntimeError(resp.error.message)
    return (
        resp.full_text_annotation.text
        or (resp.text_annotations[0].description if resp.text_annotations else "")
    )

# API 엔드포인트 !!!
@app.post("/api/ocr-receipt", response_model=OCRResult)
async def ocr_receipt(
    file: UploadFile = File(...),
    memo: Optional[str] = Form(default=None)
):
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(400, "빈 파일입니다.")
        if len(content) > 8 * 1024 * 1024:
            raise HTTPException(413, "이미지 크기가 너무 큽니다(>8MB).")

        text = run_vision_ocr(content)
        lines = normalize(text)

        merchant = extract_merchant(lines)
        amount = extract_amount(text)
        date = extract_date(text)
        items = extract_items(lines)
        cat = suggest_category(merchant, items, memo)

        return OCRResult(
            merchant=merchant,
            amount=amount,
            date=date,
            items=items,
            suggested_category=cat,
            raw_text=text
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, f"OCR 처리 중 오류: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}

# 개발용 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
