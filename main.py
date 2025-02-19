import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_wtf.file import FileAllowed
from flask_admin.form import FileUploadField

# 创建 Flask 应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///faces.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'  # Flask-Admin 需要

db = SQLAlchemy(app)
admin = Admin(app, name='工人管理后台', template_mode='bootstrap3')

# 确保目录存在
UPLOAD_FOLDER = "static/known_faces"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 工人数据库模型
class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    photo_path = db.Column(db.String(200), nullable=False)  # 存储图片文件名

    def __repr__(self):
        return f'<Worker {self.name}>'

# 自定义 Admin 视图，支持文件上传
import face_recognition
import cv2


class WorkerAdmin(ModelView):
    form_extra_fields = {
        "photo_path": FileUploadField(
            "Photo",
            base_path=UPLOAD_FOLDER,
            allowed_extensions=["jpg", "jpeg", "png"],
            namegen=lambda model, file_data: f"{model.name}{os.path.splitext(file_data.filename)[1]}"
        )
    }

    def on_model_delete(self, model):
        """ 删除数据库记录时，自动删除照片文件 """
        if model.photo_path:
            file_path = os.path.join(UPLOAD_FOLDER, model.photo_path)
            if os.path.exists(file_path):
                os.remove(file_path)  # 删除文件
                print(f"已删除照片文件: {file_path}")

    def on_model_change(self, form, model, is_created):
        """ 在图片上传后，自动裁剪人脸 """
        image_path = os.path.join(UPLOAD_FOLDER, model.photo_path)

        # 读取图片
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)

        if face_locations:
            # 取第一张脸
            top, right, bottom, left = face_locations[0]
            face_image = image[top:bottom, left:right]

            # 转换为 OpenCV 格式
            face_image_cv2 = cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(image_path, face_image_cv2)  # 覆盖原图片

admin.add_view(WorkerAdmin(Worker, db.session))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000, debug=True)