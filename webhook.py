from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def receive_data():
    """接收简道云推送的数据"""
    data = request.json  # 获取推送过来的 JSON 数据

    # 打印日志，验证数据格式
    print("收到简道云推送的数据:", data)

    # 返回确认响应
    return jsonify({"status": "success", "message": "Data received"}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8099, debug=True)