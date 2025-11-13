# client_demo.py
import requests


payload = {
    "user_id": "u_123",
    "messages": [
        {"role": "user", "content": "이번 달 커피 지출 총합 알려줘"}
    ]
}


r = requests.post("http://127.0.0.1:9000/chat", json=payload, timeout=60)
print(r.json())

# client_demo.py


payload = {
    "user_id": "u_123",
    "messages": [
        {"role": "user", "content": "이번 달 커피 지출 총합 알려줘"}
    ]
}


r = requests.post("http://127.0.0.1:9000/chat", json=payload, timeout=60)
print(r.json())
