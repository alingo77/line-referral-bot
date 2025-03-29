@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("[Webhook ERROR]", e)
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

        except Exception as e:
            print("[綁定錯誤]", e)
            reply = "⚠️ 格式錯誤，請使用：/綁定 12345678"

        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(reply)
            )
        except Exception as e:
            print("[Reply ERROR]", e)
