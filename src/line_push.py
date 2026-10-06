"""LINE Messaging API 推播"""

import requests

PUSH_URL = "https://api.line.me/v2/bot/message/push"


def push_messages(token, to, messages):
    """推播訊息給單一對象，失敗時拋出含 LINE 回應內容的錯誤"""
    response = requests.post(
        PUSH_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={"to": to, "messages": messages},
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"LINE 推播失敗 HTTP {response.status_code}: {response.text}")
