import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.event import listens_for

db = SQLAlchemy()

# 定义 Worker 模型
class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 工人姓名
    photo_path = db.Column(db.String(255), nullable=False)  # 存储人脸照片路径

    def __repr__(self):
        return f"<Worker {self.name}>"

# 自动删除数据库记录时，同时删除文件
@listens_for(Worker, "after_delete")
def delete_worker_photo(mapper, connection, target):
    """当 Worker 记录被删除时，删除对应的照片文件"""
    if target.photo_path:
        try:
            os.remove(target.photo_path)
        except Exception as e:
            print(f"⚠️ 删除文件失败: {target.photo_path} - {e}")