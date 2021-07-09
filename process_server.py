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
import json
import imagezmq
import numpy
import base64

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info('Initializing Processing...')
dictLastCameraTrigger = {}
dictCameraProcessingDelay = {}
context = zmq.Context()

logger.info('connecting to all sockets')


image_hub = imagezmq.ImageHub(open_port='tcp://127.0.0.1:6000', REQ_REP=False)

image_hub.connect('tcp://127.0.0.1:6001')
image_hub.connect('tcp://127.0.0.1:6002')
image_hub.connect('tcp://127.0.0.1:6003')

time.sleep(1)

dest_queue=imagezmq.ImageSender(connect_to='tcp://0.0.0.0:5557', REQ_REP=False)
logger.info('CONNECT complete')

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
                
                
                data, frame = image_hub.recv_image()
                                
                cam_name = data['cam_name']
                captureTime = data['captureTime']
                
                dictLastCameraTrigger[cam_name] = captureTime
                
                currenttime = time.time()
                executiondelay  = currenttime - (dictLastCameraTrigger.get(cam_name, currenttime) ) 
                lastMaxDelay = dictCameraProcessingDelay.get(cam_name,1)
                logger.info("execution delay:%.4f maxdelay : %.4f",executiondelay,lastMaxDelay)
                if(executiondelay > lastMaxDelay  ):

                        dictCameraProcessingDelay[cam_name]= executiondelay
                
                totalprocessedImages+=1

                
                logger.info('Processing - camera name: %s capture time: %s totalimagesprocessed :%d', cam_name, captureTime,totalprocessedImages)

                
                eventid =1
                file_name = "{0}{1}-{2}-{3}.{4}".format(bas_dir,cam_name,eventid,time.strftime("%Y%m%d-%H%M%S"),"jpg")

                #cv2.imwrite(file_name, frame)
                
                
                frame = detect_people(frame)

                if frame is not None:

                        
                        eventid=+1

                        

                        
                        
                        data = {"cam_name": cam_name, "captureTime":captureTime }
                        dest_queue.send_image(data,frame)

                        #file_name = "{0}{1}-{2}-{3}.{4}".format(bas_dir,cam_name,eventid,time.strftime("%Y%m%d-%H%M%S"),"jpg")

                        #cv2.imwrite(file_name, frame)

                        
                #time.sleep(0.04)

                

except (KeyboardInterrupt, SystemExit):
        processingEndTime = datetime.datetime.now()
        timeduration = processingEndTime - startimeofImageProcessing
        
        logger.info('Total images processed :%d Duration :%s',totalprocessedImages,timeduration)
        print(dictCameraProcessingDelay)
        logger.info('System exiting...')
        pass

except Exception as ex:
        
        logger.info("Python error with no Exception handler")

        logger.info('Traceback error: %s', ex)
        
        traceback.print_exc()

finally:
        
        sys.exit()
