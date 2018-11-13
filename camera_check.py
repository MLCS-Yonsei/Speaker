import cv2
import numpy as np
import matplotlib.pyplot as plt
import sys
# from utils import *
# sys.path.insert(0, './bin/hand_tracking')
# from hand_tracking.utils import detector_utils as detector_utils
"""Camera calibration"""
'''
def crop_img(img,box):
    y,x,d = img.shape
    startx = int(x*box[0])
    starty = int(y*box[1])
    endx = int(x*box[3])
    endy = int(y*box[2])

    return img[starty:endy,startx:endx]

# Create a VideoCapture object
cap = cv2.VideoCapture(1)
# Check if camera opened successfully
if (cap.isOpened() == False): 
  print("Unable to read camera feed")
 
# Default resolutions of the frame are obtained.The default resolutions are system dependent.
# We convert the resolutions from float to integer.
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
 
# Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.

while(True):
  ret, frame = cap.read()
 
  if ret == True: 
    image_cropped = crop_img(frame, np.array([0.32,0.06,0.9,0.65]))
    # print(image_cropped.shape)
    plt.imshow(image_cropped)
    plt.show()
    # Write the frame into the file 'output.avi'
    # Display the resulting frame    
    cv2.imshow('frame',frame)
 
    # Press Q on keyboard to stop recording
    if cv2.waitKey(1) & 0xFF == ord('q'):
      break
 
  # Break the loop
  else:
    break 
 
# When everything done, release the video capture and video write objects
cap.release()

# Closes all the frames
cv2.destroyAllWindows() 
'''


"""Check camera index"""

# Create a VideoCapture object
cap = cv2.VideoCapture(0)
# Check if camera opened successfully
if (cap.isOpened() == False): 
  print("Unable to read camera feed")
 
# Default resolutions of the frame are obtained.The default resolutions are system dependent.
# We convert the resolutions from float to integer.
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
 
# Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.

while(True):
  ret, frame = cap.read()
 
  if ret == True: 
    
    # Write the frame into the file 'output.avi'
    # Display the resulting frame    
    cv2.imshow('frame',frame)
 
    # Press Q on keyboard to stop recording
    if cv2.waitKey(1) & 0xFF == ord('q'):
      break
 
  # Break the loop
  else:
    break 
 
# When everything done, release the video capture and video write objects
cap.release()

# Closes all the frames
cv2.destroyAllWindows() 


"""Check hand position"""
'''
def detect_hand(cam):
    # Hands Detection
    detection_graph, sess = detector_utils.load_inference_graph()

    start_time = datetime.datetime.now()
    num_frames = 0
    (im_width, im_height) = cam.shape()
    # max number of hands we want to detect/track
    num_hands_detect = 2
    ready_cnt = 0

    while True:
        # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
        ret, image_np = cam.read()
        try:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        except:
            print("Error converting to RGB")

        # actual detection
        boxes, scores = detector_utils.detect_objects(
            image_np, detection_graph, sess)

        # draw bounding boxes
        detector_utils.draw_box_on_image(
            num_hands_detect, 0.2, scores, boxes, im_width, im_height, image_np)
        print(im_height)
        ready_hands_cnt = 0
        
        for i in range(num_hands_detect):
            (left, right, top, bottom) = (boxes[i][1] * im_width, boxes[i][3] * im_width,
                                          boxes[i][0] * im_height, boxes[i][2] * im_height)
            # print(left, right, top, bottom)
            if left > 155 and right < 540 and top > 300 and bottom < 490:
                ready_hands_cnt += 1
            
            # print(ready_hands_cnt)

        if ready_hands_cnt >= 1:
            ready_cnt += 1
        
        print(ready_hands_cnt, ready_cnt)
        if ready_cnt > 10:
            return True
        # Calculate Frames per second (FPS)
        num_frames += 1
        elapsed_time = (datetime.datetime.now() -
                        start_time).total_seconds()
        fps = num_frames / elapsed_time
        
        cam.show(cv2.cvtColor(
            image_np, cv2.COLOR_RGB2BGR))

        if cv2.waitKey(25) & 0xFF == ord('q'):
            return False
        
class Cam():
    def __init__(self, device_id, display=True):
        self.cam = cv2.VideoCapture(int(device_id))   

        if display:
            self.window_name = 'Cam'+str(device_id)
            cv2.namedWindow(self.window_name)
            # cv2.setMouseCallback(self.window_name,mouse_callback)

        if self.cam.isOpened() == False:
            print('Can\'t open the CAM(%d)' % (CAM_ID))
            exit()
cam = Cam(0)
detect_hand(cam)
'''

# $ lsusb => check *** of '/dev/bus/usb/001/***'
# $ udevadm info --query=property --name /dev/bus/usb/001/010  or $ udevadm info -q path -n /dev/bus/usb/001/010 => check devpath 
'''
import pyudev
context = pyudev.Context()

for device in context.list_devices(subsystem='usb'):
    if device.get('DEVPATH') == '/devices/pci0000:00/0000:00:14.0/usb1/1-7/1-7.4':
        # var['cam_id'] = 0   #192.168.0.2
        ip02 = device.get('DEVNUM')
    
    elif device.get('DEVPATH') == '/devices/pci0000:00/0000:00:14.0/usb1/1-8/1-8.4':
        # var['cam_id'] = 1   #192.168.0.52
        ip52 = device.get('DEVNUM')
'''
