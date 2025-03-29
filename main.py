# main.py

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import firebase_admin
from firebase_admin import credentials, db
import datetime
import os
import json

# ====== 環境變數設定 ======
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
firebase_key_json = os.getenv("FIREBASE_KEY_JSON")

# ====== 初始化 Flask 與 LINE Bot ======
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ====== Firebase 初始化 ======
try:
    firebase_key_dict = json.loads(firebase_key_json)
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://line-referral-bot-default-rtdb.asia-southeast1.firebasedatabase.app/'  # 改為你自己的 URL
    })
    print("✅ Firebase 初始化成功")
except Exception as e:
    print("❌ Firebase 初始化失敗:", e)

# ====== Webhook 接收 ======
@app.route("/callback", methods=['POST'])

def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    print("[Webhook] Signature:", signature)
    print("[Webhook] Body:", body)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("[Webhook ERROR]", e)
        abort(400)

    return 'OK', 200


# ====== 處理訊息事件 ======
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()
    line_id = event.source.user_id

    if msg.startswith("/綁定"):
        try:
            parts = msg.split()
            if len(parts) != 2:
                raise ValueError("格式錯誤")
            downline_uid = parts[1]

            inviter_uid = get_inviter_uid_by_line_id(line_id)
            if not inviter_uid:
                reply = "⚠️ 無法識別你的身份，請先聯絡管理員登記 LINE ID"
            else:
                ref = db.reference(f'users/{downline_uid}')
                ref.set({
                    "inviter_uid": inviter_uid,
                    "created_at": datetime.datetime.utcnow().isoformat()
                })
                reply = f"✅ 成功綁定下線 UID：{downline_uid}"

        except Exception as e:
            print("[綁定指令錯誤]", e)
            reply = "⚠️ 格式錯誤，請使用：/綁定 12345678"

        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(reply)
            )
        except Exception as e:
            print("[Reply 發送失敗]", e)

# ====== 模擬合夥人對照表（正式版請改從資料庫讀取） ======
def get_inviter_uid_by_line_id(line_id):
    mock_mapping = {
        "Uxxx1": "A123456",
        "Uxxx2": "B999999"
    }
    return mock_mapping.get(line_id)

# ====== 啟動伺服器（開發用） ======
if __name__ == "__main__":
    app.run()
