import hmac
import hashlib
import json
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)

# 你的 Secret Key（与简道云中配置的一样）
SECRET_KEY = "ML4GckSD4Tau4upwdTjF2fEn"

# 用于验证签名的函数
def verify_signature(secret, data, signature, timestamp, nonce):
    """ 验证请求签名 """
    content = f"{nonce}:{data.decode('utf-8')}:{secret}:{timestamp}"
    expected_signature = hmac.new(secret.encode(), content.encode('utf-8'), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

# 处理收到的数据
def handle(payload):
    # 在这里添加处理逻辑（例如添加、更新或删除数据等）
    print("Processing payload:", payload)
    # 示例: 处理 op 为 'data_create' 的数据
    if payload.get('op') == 'data_create':
        print("New data received:", payload['data'])

# Webhook 接收路由
@app.route("/webhook", methods=["POST"])
def webhook():
    # 获取请求体数据
    raw_data = request.get_data()

    # 获取简道云传过来的签名、时间戳和nonce
    received_signature = request.headers.get("X-JDY-Signature", "")
    timestamp = request.args.get("timestamp", "")
    nonce = request.args.get("nonce", "")

    # 验证签名
    if not verify_signature(SECRET_KEY, raw_data, received_signature, timestamp, nonce):
        return jsonify({"status": "error", "message": "Invalid signature"}), 403

    # 解析 JSON 数据
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        return jsonify({"status": "error", "message": "Invalid JSON data"}), 400

    # 异步处理数据
    threading.Thread(target=handle, args=(data,)).start()

    return jsonify({"status": "success"})

if __name__ == "__main__":
    # 在所有地址上运行 Flask 应用，使用生产模式
    app.run(host="0.0.0.0", port=8099, debug=False)