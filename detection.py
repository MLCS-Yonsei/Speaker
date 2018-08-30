import sys
import os
import time

sys.path.insert(0, './bin')
import numpy as np
import tensorflow as tf
from matplotlib import pyplot as plt
from PIL import Image
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

from sort.sort import *
from color_extractor.color_extractor import ImageToColor

from controllers.ageGenderController import *

from multiprocessing import Process, Queue

sys.path.insert(0, './bin/tf_openpose')
from tf_pose.estimator import TfPoseEstimator
from tf_pose.networks import get_graph_path, model_wh

# from age_gender.age_gender_main import *

from utils import *
sys.path.insert(0, './bin/hand_tracking')
from hand_tracking.utils import detector_utils as detector_utils

import cv2
import datetime

def detect_gender(image):
    face_detect = face_detection_model('dlib', './bin/age_gender/Model/shape_predictor_68_face_landmarks.dat')
    faces, face_files, rectangles, tgtdir = face_detect.run(image)

    return gender_estimate(face_files, image, tgtdir)

def detect_human(cam):
    CWD_PATH = os.getcwd()
    CWD_PATH = os.path.abspath(os.path.join(CWD_PATH, os.pardir))
    CWD_PATH = os.path.join(CWD_PATH, '3_BRobot')

    # Path to frozen detection graph. This is the actual model that is used for the object detection.
    MODEL_NAME = 'ssd_mobilenet_v1_coco_2017_11_17'
    PATH_TO_CKPT = os.path.join(CWD_PATH, 'object_detection', MODEL_NAME, 'frozen_inference_graph.pb')

    # List of the strings that is used to add correct label for each box.
    PATH_TO_LABELS = os.path.join(CWD_PATH, 'object_detection', 'data', 'mscoco_label_map.pbtxt')

    NUM_CLASSES = 90
    prevTime = 0

    # Loading label map
    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                                use_display_name=True)
    category_index = label_map_util.create_category_index(categories)

    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')

    with detection_graph.as_default():
        with tf.Session(graph=detection_graph) as sess:
            # Load modules
            mot_tracker = Sort() 
            cnt = 0

            while (True):
                ret, frame = cam.read()

                # Detection
                image_process, person_box = detect_objects(frame, sess, detection_graph, category_index, mot_tracker)
                
                if person_box.any() is not False:
                    cnt += 1

                curTime = time.time()
                sec = curTime - prevTime
                prevTime = curTime
                fps = 1 / (sec)

                str1 = "FPS : %0.1f" % fps
                str2 = "Detecting Human . . ."
                cv2.putText(frame, str1, (5, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0))
                cv2.putText(frame, str2, (100, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0))
                cam.show(frame)

                if cnt > 10:
                    return crop_img(frame, person_box)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                # plt.figure(figsize=IMAGE_SIZE)
                # plt.imshow(image_process)
                # plt.show()

            return False

def detect_objects(image_np, sess, detection_graph, category_index, mot_tracker):
    # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
    image_np_expanded = np.expand_dims(image_np, axis=0)
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

    # Each box represents a part of the image where a particular object was detected.
    boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

    # Each score represent how level of confidence for each of the objects.
    # Score is shown on the result image, together with the class label.
    scores = detection_graph.get_tensor_by_name('detection_scores:0')
    classes = detection_graph.get_tensor_by_name('detection_classes:0')
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')

    # Actual detection.
    (boxes, scores, classes, num_detections) = sess.run(
        [boxes, scores, classes, num_detections],
        feed_dict={image_tensor: image_np_expanded})

    trackers = mot_tracker.update(boxes[0])
    
    person_ids = [i for i, e in enumerate(classes[0]) if e == 1]

    if len(person_ids) > 0:
        selected_person_id = person_ids[0]
        
        person_box = boxes[0][selected_person_id]
        person_score = scores[0][selected_person_id]
        person_tracker = trackers[selected_person_id]

        if person_score > 0.6:
            person_attr = {
                'age':'NA',
                'gender':'NA',
                'color':'NA'
            }
            # print(person_attr)
            # override boxes
            boxes = np.expand_dims(person_box, axis=0)
            classes = [1]
            scores = np.expand_dims(person_score, axis=0)
            trackers = np.expand_dims(person_tracker, axis=0)
            person_attr = [person_attr]

            # Visualization of the results of a detection.
            vis_util.visualize_boxes_and_labels_on_image_array(
                image_np,
                boxes,
                classes,
                scores,
                trackers,
                person_attr,
                category_index,
                use_normalized_coordinates=True,
                line_thickness=3)
        
        return image_np, person_box

    return image_np, False

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

        ready_hands_cnt = 0
        
        for i in range(num_hands_detect):
            (left, right, top, bottom) = (boxes[i][1] * im_width, boxes[i][3] * im_width,
                                          boxes[i][0] * im_height, boxes[i][2] * im_height)

            if left > 500 and right < 1000 and top > 450 and bottom < 720:
                ready_hands_cnt += 1

        if ready_hands_cnt == 2:
            ready_cnt += 1
        
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

def crop_img(img,box):
    y,x,d = img.shape
    startx = int(x*box[0])
    starty = int(y*box[1])
    endx = int(x*box[3])
    endy = int(y*box[2])

    return img[starty:endy,startx:endx]

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

    def read(self):
        return self.cam.read()

    def show(self, frame):
        cv2.imshow(self.window_name, frame)

    def shape(self):
        return (self.cam.get(3), self.cam.get(4))

    def close(self):
        self.cam.release()
        cv2.destroyWindow(self.window_name)

        