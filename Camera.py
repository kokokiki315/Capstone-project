#Import opencv
import cv2
#Import matplotlib
from matplotlib import pyplot as plt
from ultralytics import YOLO
import datetime

#https://docs.ultralytics.com/modes/track/#why-choose-ultralytics-yolo-for-object-tracking
# Load a model
model = YOLO("yolo11s.pt")  # load an official detection model
#https://github.com/ultralytics/notebooks/blob/main/notebooks/how-to-track-the-objects-in-zone-using-ultralytics-yolo.ipynb
# Track with the model
model.track(source=0, conf=0.3, iou=0.5, show=True, tracker="bytetrack.yaml")

cam = cv2.VideoCapture(0)

# Get the default frame width and height
frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

#save the file name as current time
videoName= str(datetime.datetime.now())

# Define the codec and create VideoWriter object # https://www.geeksforgeeks.org/python/saving-a-video-using-opencv/q
out = cv2.VideoWriter(videoName+'.mp4v', cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (frame_width, frame_height))

# Define region points
dimension = [(150, 150), (1130, 150), (1130, 570), (150, 570)]

trackzone = solutions.TrackZone(show=True, region=dimension)

                                
while True:
    ret, frame = cam.read()

    results = trackzone(frame)

    # Write the frame to the output file
    out.write(frame)

    # Display the captured frame
    cv2.imshow('Camera', frame)

    # Press 's' to exit the loop
    if cv2.waitKey(1) == ord('s'):
        break

# Release the capture and writer objects
cam.release()
out.release()
cv2.destroyAllWindows()