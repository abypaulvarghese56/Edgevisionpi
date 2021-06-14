#cython: language_level=3, boundscheck=False

import multiprocessing as mp
from enum import Enum
import numpy as np
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
Gst.init(None)
import time
import cv2
import zmq
from viztracer import log_sparse

'''Konwn issues

* if format changes at run time system hangs
'''
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StreamMode(Enum):
    INIT_STREAM = 1
    SETUP_STREAM = 1
    READ_STREAM = 2


class StreamCommands(Enum):
    FRAME = 1
    ERROR = 2
    HEARTBEAT = 3
    RESOLUTION = 4
    STOP = 5


class StreamCapture(mp.Process):

    def __init__(self, link, stop, outQueue, framerate,cameraName,zmqpuburl):
        """
        Initialize the stream capturing process
        link - rstp link of stream
        stop - to send commands to this process
        outPipe - this process can send commands outside
        """

        super().__init__()
        self.streamLink = link
        self.zmqcontext =None
        self.zmqSocket = None
        self.zmqpublishurl = zmqpuburl
        self.stop = stop
        self.outQueue = outQueue
        self.framerate = framerate
        self.currentState = StreamMode.INIT_STREAM
        self.pipeline = None
        self.source = None
        self.decode = None
        self.convert = None
        self.sink = None
        self.image_arr = None
        self.newImage = False
        self.frame1 = None
        self.frame2 = None
        self.num_unexpected_tot = 40
        self.unexpected_cnt = 0
        self.cameraName= cameraName


    
    def gst_to_opencv(self, sample):
        buf = sample.get_buffer()
        caps = sample.get_caps()

        
        #logger.info("New sample recveived from %s Format is %s Height:%d, width:%d", self.cameraName,format,height,width)

        arr = np.ndarray(
            (caps.get_structure(0).get_value('height'),
             caps.get_structure(0).get_value('width'),
             3),
            buffer=buf.extract_dup(0, buf.get_size()),
            dtype=np.uint8)
        return arr

    
    def new_buffer(self, sink, _):
        sample = sink.emit("pull-sample")
        
        arr = self.gst_to_opencv(sample)
                
        self.image_arr = arr
        self.newImage = True
        
        #url="Samples/" + self.cameraName + "_" + str(time.time()) +".jpg"
        #cv2.imwrite(url,arr)
        currentTime=time.time()
        caps = sample.get_caps()
        imgformat=caps.get_structure(0).get_value('format')
        height=caps.get_structure(0).get_value('height')
        width=caps.get_structure(0).get_value('width')
        logger.info("Got sample from %s as %s Height:%d, width:%d . capture time: %s", self.cameraName,imgformat,height,width,str(currentTime))
        self.zmqSocket.send_pyobj(dict(frame=arr, cam_name=self.cameraName, captureTime=currentTime))
        return Gst.FlowReturn.OK

    
    def run(self):
        pipelinestring = "rtspsrc location={0}  latency=100 name=m_rtspsrc ! rtph264depay ! h264parse ! v4l2h264dec capture-io-mode=4 ! video/x-raw ! v4l2convert output-io-mode=5 capture-io-mode=4  ! video/x-raw,  format=(string)BGR,  width=(int)640, height=(int)480  ! videorate ! video/x-raw,framerate=1/1 ! appsink name=m_appsink sync=false".format(self.streamLink)
        
        
        self.pipeline = Gst.parse_launch(pipelinestring)
        self.source = self.pipeline.get_by_name('m_rtspsrc')
        
        
        # sink params
        self.sink = self.pipeline.get_by_name('m_appsink')

        # Maximum number of nanoseconds that a buffer can be late before it is dropped (-1 unlimited)
        # flags: readable, writable
        # Integer64. Range: -1 - 9223372036854775807 Default: -1
        self.sink.set_property('max-lateness', 500000000)

        # The maximum number of buffers to queue internally (0 = unlimited)
        # flags: readable, writable
        # Unsigned Integer. Range: 0 - 4294967295 Default: 0
        self.sink.set_property('max-buffers', 5)

        # Drop old buffers when the buffer queue is filled
        # flags: readable, writable
        # Boolean. Default: false
        self.sink.set_property('drop', 'true')

        # Emit new-preroll and new-sample signals
        # flags: readable, writable
        # Boolean. Default: false
        self.sink.set_property('emit-signals', True)

        
        self.sink.connect("new-sample", self.new_buffer, self.sink)

        # Start playing
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("Unable to set the pipeline to the playing state.")
            self.stop.set()

        # Wait until error or EOS
        bus = self.pipeline.get_bus()
        
        self.zmqcontext = zmq.Context()
        self.zmqSocket = self.zmqcontext.socket(zmq.PUB)
        self.zmqSocket.bind(self.zmqpublishurl)

        while True:

            time.sleep(2)
            if self.stop.is_set():
                print('Stopping CAM Stream by main process')
                break

            message = bus.timed_pop_filtered(10000, Gst.MessageType.ANY)
            # print "image_arr: ", image_arr
            if self.image_arr is not None and self.newImage is True:

                self.image_arr = None
                self.unexpected_cnt = 0


            if message:
                if message.type == Gst.MessageType.ERROR:
                    err, debug = message.parse_error()
                    print("Error received from element %s: %s" % (
                        message.src.get_name(), err))
                    print("Debugging information: %s" % debug)
                    break
                elif message.type == Gst.MessageType.EOS:
                    print("End-Of-Stream reached.")
                    break
                elif message.type == Gst.MessageType.STATE_CHANGED:
                    if isinstance(message.src, Gst.Pipeline):
                        old_state, new_state, pending_state = message.parse_state_changed()
                        print("Pipeline state changed from %s to %s." %
                              (old_state.value_nick, new_state.value_nick))
                else:
                    print("Unexpected message received.")
                    self.unexpected_cnt = self.unexpected_cnt + 1
                    #if self.unexpected_cnt == self.num_unexpected_tot:
                        #break


        print('terminating cam pipe')
        self.stop.set()
        self.pipeline.set_state(Gst.State.NULL)
