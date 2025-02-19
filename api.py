import os
import cv2
import numpy as np
import face_recognition
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# 数据库配置
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/faces.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# 目录配置
KNOWN_FACES_DIR = "static/known_faces"  # 存储已知工人照片
TEMP_DIR = "static/temp"  # 存储临时上传照片
THRESHOLD = 0.7  # 人脸匹配阈值

# 确保目录存在
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# 定义 Worker 模型
class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    photo_path = db.Column(db.String(200), nullable=False)

# 初始化数据库
with app.app_context():
    db.create_all()

# 载入已知人脸
def load_known_faces():
    """从数据库加载所有工人，并读取他们的照片编码"""
    known_encodings = []
    known_names = []

    with app.app_context():  # 确保在 Flask 上下文中
        workers = Worker.query.all()  # 查询所有工人

        for worker in workers:
            photo_path = os.path.join(KNOWN_FACES_DIR, worker.photo_path)
            if os.path.exists(photo_path):
                image = face_recognition.load_image_file(photo_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_encodings.append(encodings[0])
                    known_names.append(worker.name)  # 直接使用数据库里的姓名

    return known_encodings, known_names

# 初始化已知人脸
known_encodings, known_names = load_known_faces()

# 添加 PIL 方式绘制中文
def draw_text_chinese(image_cv2, text, position, color=(0, 255, 0), font_size=24):
    """ 在图片上绘制中文文本 """
    pil_image = Image.fromarray(cv2.cvtColor(image_cv2, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_image)

    # 选择字体（macOS 宋体，Windows 需要改成 `C:/Windows/Fonts/simhei.ttf`）
    font_path = "/System/Library/Fonts/Supplemental/Songti.ttc"  # macOS 宋体
    font = ImageFont.truetype(font_path, font_size)

    draw.text(position, text, font=font, fill=color)
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

# 单人比对 API
@app.route("/compare", methods=["POST"])
def compare_faces():
    """ 接收上传图片，与已知人脸比对 """
    if "file" not in request.files:
        return jsonify({"error": "未检测到文件"}), 400

    file = request.files["file"]
    image_path = os.path.join(TEMP_DIR, file.filename)
    file.save(image_path)

    # 读取上传图片
    unknown_image = face_recognition.load_image_file(image_path)
    unknown_encodings = face_recognition.face_encodings(unknown_image)

    if not unknown_encodings:
        return jsonify({"error": "未检测到人脸"}), 400

    unknown_encoding = unknown_encodings[0]

    # 进行比对
    results = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=THRESHOLD)
    distances = face_recognition.face_distance(known_encodings, unknown_encoding)

    best_match_index = np.argmin(distances) if results else None

    if best_match_index is not None and results[best_match_index]:
        match_result = "匹配"
        name = known_names[best_match_index]
    elif best_match_index is not None and distances[best_match_index] < 0.8:
        match_result = "可能"
        name = known_names[best_match_index]
    else:
        match_result = "未匹配"
        name = "未知"

    return jsonify({
        "match": match_result,
        "matched_person": name
    })

# 群体人脸识别 API
@app.route("/group_recognition", methods=["POST"])
def group_recognition():
    """ 处理集体合照，识别劳务工人，并在图片中标注 """
    if "file" not in request.files:
        return jsonify({"error": "未检测到文件"}), 400

    file = request.files["file"]
    image_path = os.path.join(TEMP_DIR, file.filename)
    file.save(image_path)

    # 读取图片
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    if not face_encodings:
        return jsonify({"error": "未检测到人脸"}), 400

    # 载入 OpenCV 版本的图片用于标注
    image_cv2 = cv2.imread(image_path)

    results_list = []
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        # 计算所有已知人脸的相似度
        distances = face_recognition.face_distance(known_encodings, face_encoding)
        best_match_index = np.argmin(distances)
        best_distance = distances[best_match_index]

        if best_distance < 0.65:
            match_text = "匹配"
            color = (0, 255, 0)  # 绿色 ✅
            name = known_names[best_match_index]
        elif best_distance < 0.8:
            match_text = "可能"
            color = (0, 255, 255)  # 黄色 ⚠️
            name = known_names[best_match_index]
        else:
            match_text = "未匹配"
            color = (0, 0, 255)  # 红色 ❌
            name = "未知"

        # 记录结果
        results_list.append({
            "name": name,
            "match_result": match_text
        })

        # 绘制人脸框和匹配结果
        cv2.rectangle(image_cv2, (left, top), (right, bottom), color, 2)
        label = f"{name} - {match_text}"
        image_cv2 = draw_text_chinese(image_cv2, label, (left, top - 30), color)

    # 保存带标注的图片
    output_path = os.path.join(TEMP_DIR, f"processed_{file.filename}")
    cv2.imwrite(output_path, image_cv2)

    return send_file(output_path, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099, debug=True)