#Import opencv
import cv2
#Import matplotlib
from matplotlib import pyplot as plt

import datetime

cam = cv2.VideoCapture(0)

# Get the default frame width and height
frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

#save the file name as current time
videoName= str(datetime.datetime.now())

# Define the codec and create VideoWriter object # https://www.geeksforgeeks.org/python/saving-a-video-using-opencv/q
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(videoName+'.mp4v', fourcc, 20.0, (frame_width, frame_height))

while True:
    ret, frame = cam.read()

    # Write the frame to the output file
    out.write(frame)

    # Display the captured frame
    cv2.imshow('Camera', frame)

    # Press 'q' to exit the loop
    if cv2.waitKey(1) == ord('s'):
        break

# Release the capture and writer objects
cam.release()
out.release()
cv2.destroyAllWindows()