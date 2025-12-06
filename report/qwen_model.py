# 코드 작성일 25/11/21
# qwen_model.py
import os
import json
from typing import List, Dict, Any, Optional
from transformers import BitsAndBytesConfig

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv

load_dotenv()

# .env에 없으면 기본값으로 1.5B instruct 모델 사용
MODEL_NAME = os.getenv("CHATBOT_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")

_tokenizer = None
_model = None

def get_qwen_model():
    global _tokenizer, _model
    if _model is None:
        print(f"[Qwen] Loading model: {MODEL_NAME}")
        # change 16bit to 4bit
        # quantization_config = BitsAndBytesConfig(
        #     load_in_4bit=True,
        #     bnb_4bit_compute_dtype=torch.float16,
        #     bnb_4bit_use_double_quant=True,
        # )

        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype="auto",
            # quantization_config=quantization_config, # 설정 적용
            device_map="auto",
        )
    return _tokenizer, _model


def generate_spending_report(
    transactions: List[Dict[str, Any]],
    user_question: Optional[str] = None,
) -> str:
    """
    Qwen 모델을 사용해서 소비 리포트를 생성하는 함수.
    - transactions: DB나 JSON에서 가져온 거래 내역 리스트
    - user_question: 사용자가 원하는 질문/리포트 타입
    """
    tokenizer, model = get_qwen_model()

    if not user_question:
        user_question = (
            "이 소비 내역을 바탕으로 기간별/카테고리별 요약, "
            "지출 패턴 분석, 절약을 위한 한두 가지 조언을 포함한 "
            "리포트를 줄글 형식으로 작성하십시오."
        )

    transactions_json = json.dumps(transactions, ensure_ascii=False, indent=2)

    system_prompt = (
        "당신은 개인 가계부 서비스 'OpenWallet'의 소비 분석 리포트 생성가입니다. "
        "입력으로 주어지는 JSON 형식의 거래 내역을 이해하고, "
        "특정한 데이터 형식이 읽고 좋은 텍스트(줄글)로 작성하십시오. "
        "가능하면 항목별 합계, 카테고리별 통계, 소비 패턴 요약, "
        "절약/개선 팁 등을 포함하고, 중요한 수치는 숫자로 명확하게 보여주세요."
    )

    user_content = (
        f"요청사항: {user_question}\n\n"
        "다음은 분석해야 할 거래 내역 데이터입니다:\n"
        f"{transactions_json}\n\n"
        "위 데이터를 바탕으로 분석 보고서를 작성하세요. "
        "데이터 자체를 다시 보여주지 말고, 해석된 내용만 텍스트로 출력하세요."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    # Qwen의 chat 템플릿 사용 (transformers에서 제공)
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=800,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )

    # 프롬프트 길이만큼 잘라내고 생성된 부분만 디코딩
    gen_ids = outputs[0, inputs["input_ids"].shape[1]:]
    report = tokenizer.decode(gen_ids, skip_special_tokens=True)

    return report.strip()
