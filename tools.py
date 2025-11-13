# tools.py
from datetime import datetime
from collections import defaultdict
from typing import List, Optional, Dict


# --- Mock 데이터: (실서비스에서는 DB로 대체)
RECEIPTS = [
    # user_id, purchased_at(YYYY-MM-DD), merchant_id, category_id, total_amount
    ("u_123", "2025-11-01", 10, 21, 4500),  # 카페
    ("u_123", "2025-11-03", 10, 21, 6100),  # 카페
    ("u_123", "2025-11-10", 11, 7, 38000),  # 마트
    ("u_123", "2025-10-11", 10, 21, 5200),
]
MERCHANTS = {10: "스타카페", 11: "하이퍼마트"}
CATEGORIES = {21: "카페/커피", 7: "식료품"}


def _in_range(d: str, start: str, end: str) -> bool:
    return (start <= d) and (d < end)


def get_total_spend(user_id: str, start_date: str, end_date: str,
                    category_ids: Optional[List[int]] = None,
                    merchant_ids: Optional[List[int]] = None) -> Dict:


    s = 0
    for uid, d, mid, cid, amt in RECEIPTS:
        if uid != user_id:
            continue
        if not _in_range(d, start_date, end_date):
            continue
        if category_ids and cid not in category_ids:
            continue
        if merchant_ids and mid not in merchant_ids:
            continue
        s += amt
    return {"total": s, "currency": "KRW"}


def get_top_merchants(user_id: str, start_date: str, end_date: str,
                      limit: int = 5, category_ids: Optional[List[int]] = None) -> Dict:


    agg = defaultdict(int)
    for uid, d, mid, cid, amt in RECEIPTS:
        if uid != user_id or not _in_range(d, start_date, end_date):
            continue
        if category_ids and cid not in category_ids:
            continue
        agg[mid] += amt
    ranked = sorted(agg.items(), key=lambda x: x[1], reverse=True)[:limit]
    result = [{"merchant_id": mid, "merchant_name": MERCHANTS.get(
        mid, str(mid)), "amount": amt} for mid, amt in ranked]
    return {"top_merchants": result, "currency": "KRW"}


def get_trend(user_id: str, period: str = "monthly", months: int = 6,
              category_ids: Optional[List[int]] = None) -> Dict:

    # 단순 mock: YYYY-MM 단위 합계
    box = defaultdict(int)
    for uid, d, mid, cid, amt in RECEIPTS:
        if uid != user_id:
            continue
        if category_ids and cid not in category_ids:
            continue
        ym = d[:7]
        box[ym] += amt
    series = sorted([{"period": k, "amount": v}
                    for k, v in box.items()], key=lambda x: x["period"])
    return {"series": series, "currency": "KRW"}
