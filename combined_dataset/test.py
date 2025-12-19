#"C:\Users\jy\Desktop\Capstone project\runs\detect\train_dataset1\weights\best.pt"
from ultralytics import YOLO

model = YOLO("C:/Users/jy/Desktop/Capstone project/yolov8n.pt")  # your trained model
results = model.predict(source=0, show=True, conf=0.5) 
