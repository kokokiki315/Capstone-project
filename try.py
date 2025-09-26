import cv2
from ultralytics import YOLO
import datetime

model = YOLO("yolo11s.pt")

cam = cv2.VideoCapture(0)

try: 
    cam.isOpened()
except:
  print("No Camera Dectected")

w=int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
h=int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

#save the file name as current time
videoName= str(datetime.datetime.now())

# Video writer
video_writer = cv2.VideoWriter(videoName+'.mp4v',
                               cv2.VideoWriter_fourcc(*"mp4v"),
                               20.0, (w, h))

# Process video
while cam.isOpened():
    success, frame = cam.read()

    cv2.rectangle(frame, (100, h-150), (w-100, h), (255, 255, 0), 2)

    if not success:
        print("Frame Error")
        break
    #https://docs.ultralytics.com/modes/track/#features-at-a-glance
    results = model.track(frame, conf=0.3, iou=0.5, persist=True)  # track the objects

    annotated_frame = results[0].plot()

    cv2.imshow('Camera' , annotated_frame)

    # Break the loop if 's' is pressed
    if cv2.waitKey(1) & 0xFF == ord('s'):
        break

cam.release()   # Release the capture
cv2.destroyAllWindows()