# main.py
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import firebase_admin
from firebase_admin import credentials, db
import datetime
import os
import json

# 從環境變數讀取 LINE Token 和 Secret
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 從環境變數讀取 Firebase JSON（整份當字串貼進 Railway）
firebase_key_json = os.getenv("FIREBASE_KEY_JSON")
firebase_key_dict = json.loads(firebase_key_json)

# Firebase 初始化
cred = credentials.Certificate(firebase_key_dict)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://line-referral-bot-default-rtdb.asia-southeast1.firebasedatabase.app/'  # 改為你自己的 Firebase DB URL
})

# LINE Bot 初始化
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except:
        abort(400)
    return 'OK'

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

        except:
            reply = "⚠️ 格式錯誤，請使用：/綁定 12345678"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(reply)
        )

# 🔒 合夥人 LINE ID 模擬對照表（之後可改用資料庫）
def get_inviter_uid_by_line_id(line_id):
    mock_mapping = {
        "Uxxx1": "A123456",
        "Uxxx2": "B999999"
    }
    return mock_mapping.get(line_id)

if __name__ == "__main__":
    app.run()
