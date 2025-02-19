import face_recognition

# 载入已知人脸
known_image = face_recognition.load_image_file("pic/known_face.png")
known_encoding = face_recognition.face_encodings(known_image)[0]  # 提取特征

# 载入未知人脸
unknown_image = face_recognition.load_image_file("pic/unknown_face.png")
unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

# 计算相似度
results = face_recognition.compare_faces([known_encoding], unknown_encoding)
if results[0]:
    print("这是同一个人！✅")
else:
    print("不是同一个人 ❌")