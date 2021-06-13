#!/usr/bin/python3
#
#
# Human detection function
#
#
#
import logging
import numpy as np
import cv2
import time
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


confidence_level = 0.85

logger.info('Loading openCV DNN module in **GPU **...')
net = cv2.dnn.readNet('person-detection-retail-0013.bin',
                     'person-detection-retail-0013.xml') #Please download these two files for the version of Intel OpenVINO that you installed in your system. 
# Specify target device.
net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)


def detect_people(frame):

        (h, w) = frame.shape[:2]
        startTick = time.time()
        #blob = cv2.dnn.blobFromImage(frame)
        #blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
        blob = cv2.dnn.blobFromImage(frame,size=(544,320),ddepth=cv2.CV_8U)
        net.setInput(blob)
        detections = net.forward()
        
        stopTick = time.time()
        elapsedTick = stopTick- startTick
        logger.info('Detection completed in %s ticks', elapsedTick)

        for detection in detections.reshape(-1, 7):
            confidence = float(detection[2])
            xmin = int(detection[3] * frame.shape[1])
            ymin = int(detection[4] * frame.shape[0])
            xmax = int(detection[5] * frame.shape[1])
            ymax = int(detection[6] * frame.shape[0])
            #print(confidence)
            if confidence > confidence_level:
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color=(0, 255, 0))
                label = "PersonX:{:.2f}%".format(confidence * 100)

                #cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color=(0, 0, 255), 2)
                
                y = ymin - 15 if ymin - 15 > 15 else ymin + 15
                color=(0, 0, 255)

                cv2.putText(frame, label, (xmin, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color , 2)
                logger.info('Detected Human with confidence of %s',confidence)
                return frame

