
'''\
MIT License

Copyright (c) 2019 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.'''

import multiprocessing as mp
import time
import vid_streamv3 as vs
import cv2
import sys
import imagezmq


'''
Main class
'''
class mainStreamClass:
    def __init__(self):

        #Current Cam
        self.camProcess = None
        self.camProcess2 =None
        self.camProcess3= None
        self.camProcess4 =None
        
        self.cam_queue = None
        self.stopbit = None
        self.camlink1 = 'rtsp://<username>:<password>@192.168.1.2:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif' #Add your RTSP cam link
        self.camlink2 = 'rtsp://<username>:<password>$@192.168.1.3:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif'
        self.camlink3 = 'rtsp://<username>:<password>$@192.168.1.4:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif'
        self.camlink4 = 'rtsp://<username>:<password>$@192.168.1.5:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif'
        
        self.framerate = 1
    
    def startMain(self):

        #set  queue size
        self.cam_queue = mp.Queue(maxsize=10)

        #get all cams
        

        self.stopbit = mp.Event()
        cam1zmqUrl= "tcp://0.0.0.0:6000" #"ipc:///tmp/test.pipe1" #"tcp://0.0.0.0:6000" #"ipc:///tmp/test.pipe1" # "tcp://127.0.0.1:6000"
        cam2zmqUrl= "tcp://0.0.0.0:6001" #"ipc:///tmp/test.pipe2" #"tcp://0.0.0.0:6001" #"ipc:///tmp/test.pipe2" # "tcp://127.0.0.1:6001"
        cam3zmqUrl= "tcp://0.0.0.0:6002" #"ipc:///tmp/test.pipe3" #"tcp://0.0.0.0:6002" #"ipc:///tmp/test.pipe3" # "tcp://127.0.0.1:6002"
        cam4zmqUrl= "tcp://0.0.0.0:6003" #"ipc:///tmp/test.pipe4" #"tcp://0.0.0.0:6003" #"ipc:///tmp/test.pipe4" # "tcp://127.0.0.1:6003"
        
        self.camProcess = vs.StreamCapture(self.camlink1,
                             self.stopbit,
                             self.cam_queue,
                            self.framerate,"camera1",cam1zmqUrl)
        self.camProcess2 = vs.StreamCapture(self.camlink2,
                             self.stopbit,
                             self.cam_queue,
                            self.framerate,"camera2",cam2zmqUrl)
                            
        self.camProcess3 = vs.StreamCapture(self.camlink3,
                             self.stopbit,
                             self.cam_queue,
                            self.framerate,"camera3",cam3zmqUrl)
        
        self.camProcess4 = vs.StreamCapture(self.camlink4,
                             self.stopbit,
                             self.cam_queue,
                            self.framerate,"camera4",cam4zmqUrl)
        
        
        
        try:
            self.camProcess.start()
            time.sleep(1)
            self.camProcess2.start()
            time.sleep(1)
            self.camProcess3.start()
            time.sleep(1)
            self.camProcess4.start()

            self.camProcess.join()
            self.camProcess2.join()
            self.camProcess3.join()
        
            self.camProcess4.join()
        
            

        except KeyboardInterrupt:
            self.stopbit.set()
            print('Caught Keyboard interrupt')

        except:
            e = sys.exc_info()
            print('Caught Main Exception')
            print(e)

        self.stopCamStream()
        


    def stopCamStream(self):
        print('in stopCamStream')

        if self.stopbit is not None:
            self.stopbit.set()
            while not self.cam_queue.empty():
                try:
                    _ = self.cam_queue.get()
                except:
                    break
                self.cam_queue.close()


            self.camProcess.join()
            self.camProcess2.join()
            self.camProcess3.join()
            self.camProcess4.join()
        


if __name__ == "__main__":
    mc = mainStreamClass()
    mc.startMain()
