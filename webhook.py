import hmac
import hashlib
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# 你的 Secret Key（跟简道云里配置的一样）
SECRET_KEY = "RDxGuVTdFqNyLGwLO4525Hbn"

def verify_signature(secret, data, signature):
    """ 验证请求签名 """
    expected_signature = hmac.new(secret.encode(), data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

@app.route("/webhook", methods=["POST"])
def webhook():
    # 获取请求体
    raw_data = request.get_data()

    # 获取简道云传过来的签名
    received_signature = request.headers.get("X-JDY-Signature", "")

    # 验证签名
    if not verify_signature(SECRET_KEY, raw_data, received_signature):
        return jsonify({"status": "error", "message": "Invalid signature"}), 403

    # 解析 JSON 数据
    data = json.loads(raw_data)
    print("Received data:", data)

    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)