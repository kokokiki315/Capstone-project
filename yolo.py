from ultralytics import YOLO

# Configure the tracking parameters and run the tracker
model = YOLO("yolo11s.pt")
results = model.track(source=0, conf=0.3, iou=0.5, show=True)
#https://github.com/ultralytics/notebooks/blob/main/notebooks/how-to-track-the-objects-in-zone-using-ultralytics-yolo.ipynb