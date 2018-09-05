import cv2
import datetime
import os, errno
import time

cam_id = 0
subject_id = 0

directory = './cam/' + str(subject_id) +'/'

try:
    os.makedirs(directory)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    cv2.imwrite(directory+str(datetime.datetime.now())+'.jpg', frame)

    time.sleep(0.05)
cap.release()