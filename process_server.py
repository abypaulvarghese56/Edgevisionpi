#!/usr/bin/python3
#
#
# tool to process incoming frame for human detection
# using openCV's DNN module and MobileNet SSD on Caffemodel
#
#
#from humandetector import detect_people
from detecthumangpu import detect_people
#from utils import event_read, event_write
import logging
import cv2
import zmq
import time
import sys, traceback
import datetime
from viztracer import log_sparse

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info('Initializing Processing...')

context = zmq.Context()

logger.info('connecting to all sockets')
src = context.socket(zmq.SUB)

# src.connect("ipc:///tmp/test.pipe1")
# time.sleep(1)
# src.connect("ipc:///tmp/test.pipe2")
# time.sleep(1)
# src.connect("ipc:///tmp/test.pipe3")
# time.sleep(1)
# src.connect("ipc:///tmp/test.pipe4")

src.connect("tcp://127.0.0.1:6000")
time.sleep(1)
src.connect("tcp://127.0.0.1:6001")
time.sleep(1)
src.connect("tcp://127.0.0.1:6002")
time.sleep(1)
src.connect("tcp://127.0.0.1:6003")


time.sleep(1)
logger.info('CONNECT complete')
topicfilter = ""
src.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

dst = context.socket(zmq.PUSH)
dst.connect("tcp://127.0.0.1:5557")

#eventid = event_read()

data = None
frame = None
cam_name = None
count = None
totalprocessedImages=0
startimeofImageProcessing = datetime.datetime.now()

bas_dir = "./data/"

try:
        while True:

                if cv2.waitKey(1) == ord("q"):
                    break

                #logger.info("Waiting to get data from SRC")
                data = src.recv_pyobj()
                frame = data['frame']
                cam_name = data['cam_name']
                captureTime = data['captureTime']
                totalprocessedImages+=1

                #print("[INFO] Processing - camera number and frame number: {} - {}".format(cam_name, count))

                logger.info('Processing - camera name: %s frame number: %s totalimagesprocessed :%d', cam_name, captureTime,totalprocessedImages)

                frame = detect_people(frame)

                if frame is not None:

                        #eventid = time.time()
                        eventid=+1

                        #print("confidence: ", confidence)

                        dst.send_pyobj(dict(frame=frame, cam_name=cam_name, eventid=eventid))

                        #file_name = "{0}{1}-{2}-{3}.{4}".format(bas_dir,cam_name,eventid,time.strftime("%Y%m%d-%H%M%S"),"jpg")

                        #cv2.imwrite(file_name, frame)

                        #event_write(eventid)
                #time.sleep(0.04)

                

except (KeyboardInterrupt, SystemExit):
        processingEndTime = datetime.datetime.now()
        timeduration = processingEndTime - startimeofImageProcessing
        
        logger.info('Total images processed :%d Duration :%s',totalprocessedImages,timeduration)
        logger.info('System exiting...')
        pass

except Exception as ex:
        
        logger.info("Python error with no Exception handler")

        logger.info('Traceback error: %s', ex)
        
        traceback.print_exc()

finally:
        
        sys.exit()
