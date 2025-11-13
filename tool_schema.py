# tool_schemas.py
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_total_spend",
            "description": "기간별 총 지출 합계(KRW). category_ids/merchant_ids로 필터링 가능.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD (exclusive)"},
                    "category_ids": {"type": "array", "items": {"type": "integer"}, "nullable": True},
                    "merchant_ids": {"type": "array", "items": {"type": "integer"}, "nullable": True}
                },
                "required": ["user_id", "start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_merchants",
            "description": "기간 내 지출 상위 가맹점 Top-N",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "limit": {"type": "integer", "default": 5},
                    "category_ids": {"type": "array", "items": {"type": "integer"}, "nullable": True}
                },
                "required": ["user_id", "start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_trend",
            "description": "월별/주별 지출 추세 집계",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "period": {"type": "string", "enum": ["monthly", "weekly"], "default": "monthly"},
                    "months": {"type": "integer", "default": 6},
                    "category_ids": {"type": "array", "items": {"type": "integer"}, "nullable": True}
                },
                "required": ["user_id"]
            }
        }
    },
]
