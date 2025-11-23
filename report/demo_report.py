# demo_report.py
import json
from qwen_model import generate_spending_report

def main():
    with open("sample_transactions.json", "r", encoding="utf-8") as f:
        transactions = json.load(f)

    question = (
        "이 소비 내역 전체를 기준으로 카테고리별 합계와 비율, "
        "소비 패턴 요약, 그리고 한두 가지 절약 팁을 포함한 리포트를 작성해줘."
    )

    report = generate_spending_report(transactions, question)

    print("\n==== Qwen 리포트 ====\n")
    print(report)
    print("\n=====================\n")


if __name__ == "__main__":
    main()
