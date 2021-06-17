#!/usr/bin/python3
#
# CommsEngine Responsible for 
#     -storing the detected image as file into the ./data directory.
#     -sending the alert to Telegram channel
#
import base64
import zmq
import logging
import json
import cv2
import datetime
import telepot
import base64
import json, time
import imagezmq

from datetime import datetime


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

starttime= time.time()
dictLastCameraTrigger = {'camera1': starttime , 'camera2': starttime, 'camera3': starttime,'camera4':starttime}

bas_dir = "./data/"

def process_data():
   image_hub = imagezmq.ImageHub(open_port='tcp://127.0.0.1:5557', REQ_REP=False)

   with context.socket(zmq.PULL) as src:
      src.bind("tcp://127.0.0.1:5557")

   while True:
      
      data, image = image_hub.recv_image()

      
      cam_name = data['cam_name']
      eventid = data['eventid']

         
      ctimestr=datetime.now().isoformat(sep=' ', timespec='milliseconds')
         
      strfileurl = "{0}{1}-{2}-{3}.{4}".format(bas_dir,cam_name,eventid,ctimestr,"jpg")
         
      logger.info('Received frame with human detected from :%s . Saving File as %s',cam_name,strfileurl)
         
      cv2.imwrite(strfileurl, image)
         
      if cam_name in dictLastCameraTrigger.keys():
         lastAlertSentTime = dictLastCameraTrigger[cam_name]
         currentTime = time.time()
            
            
         timediff = (currentTime - lastAlertSentTime)
         #see if we have sent any alters within the last 10 seonds from the same camera. Send the alert only if it is more than 10 seconds
         if(timediff > 10):
            #Lets send image
         
            bot = telepot.Bot('xxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxx')#Insert your BOT Key here
            chatid='xxxxxxxxxxxxxxxx' #Insert the chat ID here . Chat ID = ID of the user to whom the message needs to be sent.
               
            captionstring = cam_name + " @ " + ctimestr
            bot.sendPhoto(chatid, photo=open(strfileurl, 'rb'),caption=captionstring)
            logger.info('Sent the image to Telegram from camera :%s',cam_name)
            dictLastCameraTrigger[cam_name] = currentTime
         else:
            logger.info('Sent alert in less than the configured.No Alert sent to the Bot from :%s ',cam_name)
      else:
         logger.info('No camera name found in the dictionary')
         

if __name__ == '__main__':
   logger.info('Starting Communication Engine..')
   process_data()

   
   

   
   
   
   
   
