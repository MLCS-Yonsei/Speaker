import cv2
import numpy as np
import matplotlib.pyplot as plt
def crop_img(img,box):
    y,x,d = img.shape
    startx = int(x*box[0])
    starty = int(y*box[1])
    endx = int(x*box[3])
    endy = int(y*box[2])

    return img[starty:endy,startx:endx]

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
