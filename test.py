import face_recognition
import cv2

# 读取图片
image = face_recognition.load_image_file("test.png")

# 检测人脸位置
face_locations = face_recognition.face_locations(image)

if face_locations:
    print(f"检测到 {len(face_locations)} 张人脸")
else:
    print("未检测到人脸")