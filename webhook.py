import hmac
import hashlib
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# 你的 Secret Key（跟简道云里配置的一样）
SECRET_KEY = "ML4GckSD4Tau4upwdTjF2fEn"


def get_signature(nonce, payload, secret, timestamp):
    """计算签名"""
    content = ':'.join([nonce, payload, secret, timestamp]).encode('utf-8')
    m = hashlib.sha1()
    m.update(content)
    signature = m.hexdigest()

    # 输出签名计算过程
    print(f"Calculated signature: {signature}")

    return signature


def verify_signature(secret, data, signature, timestamp, nonce):
    """验证请求签名"""
    expected_signature = get_signature(nonce, data, secret, timestamp)

    # 输出验证过程
    print(f"Expected signature: {expected_signature}")
    print(f"Received signature: {signature}")

    return hmac.compare_digest(expected_signature, signature)


@app.route("/webhook", methods=["POST"])
def webhook():
    # 获取请求体
    raw_data = request.get_data()

    # 获取简道云传过来的签名
    received_signature = request.headers.get("X-JDY-Signature", "")

    # 获取请求中的 nonce 和 timestamp 参数
    nonce = request.args.get('nonce', '')
    timestamp = request.args.get('timestamp', '')

    # 验证签名
    if not verify_signature(SECRET_KEY, raw_data, received_signature, timestamp, nonce):
        print("Signature verification failed")
        return jsonify({"status": "error", "message": "Invalid signature"}), 403

    # 解析 JSON 数据
    data = json.loads(raw_data)
    print("Received data:", data)

    # 根据你的需求处理数据
    # 例如，增加数据到数据库，或者其他操作

    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)