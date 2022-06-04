"""
GPShandler.py

Code to manage the Dragino GPS device

provides non-blocking access using GPSD

"""
import logging
from threading import Thread
try:
    from gps3 import agps3
except:
    import gpsd

import json
from time import time
from datetime import datetime,timedelta

DEFAULT_LOG_LEVEL=logging.INFO


class GPS:
    def __init__(self, logging_level=DEFAULT_LOG_LEVEL,threaded=True,threadDelay=0.5):

        self.logger = logging.getLogger("GPS")
        self.logger.setLevel(logging_level)
        logging.basicConfig(format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')


        self.isThreaded=threaded
        self.threadLoopDelay=threadDelay

        self.lat=None
        self.lon=None
        self.timestamp=None
        self.lastGpsReading=None
        # used to control the thread execution
        self.running=False
        self.stopped=True

    # gpsd settings - make sure gpsd is installed and running
        self.gpsd_socket = agps3.GPSDSocket()
        self.gpsd_socket.connect('127.0.0.1', 2947)
        self.gpsd_socket.watch(gpsd_protocol='json', enable=True)
        self.data_stream = agps3.DataStream()

        if self.isThreaded:
            self.gpsThread=Thread(target=self._updater)
            self.running=True
            self.stopped=False
            self.gpsThread.start()

        self.sentences={}   # cache for GPSD sentences

    def __del__(self):
        if self.isThreaded:
            self.logger.info("Stopping the GPS background thread")
            self.running=False
            while not self.stopped:
                pass
            self.logger.info("GPS updater has stopped")

    def stop(self):
        self.__del__()

    def get_gps(self):
        """
            return the cached GPS values

            update_gps() should be called frequently to keep
            these values updated

        """
        self.logger.info("get_gps(): lat %s, lon %s, timestamp: %s", self.lat, self.lon, self.timestamp)
        return self.lat, self.lon, self.timestamp, self.lastGpsReading

    def get_corrected_timestamp(self):
        """
            return the timestamp for Now

            The system time may have drifted since the last valid GPS timestamp.

            The current timestamp will be the last GPS timestamp plus the elapsed time
            since the reading was obtained (usually within a few seconds if the GPS
            has achieved a lock)

        """

        return datetime.fromtimestamp(self.timestamp)+timedelta(time()-self.lastGpsReading)

    def delay(self,Delay):
        """
        delay which does not sleep the thread

        :Param Delay: float (seconds)
        """
        start=time()
        while time()<(start+Delay):
            pass


    def _updater(self):
        """
        GPS updater thread, samples GPS typically every 0.5 seconds
        """
        while self.running:
            self.update_gps()
            self.delay(self.threadLoopDelay)
        self.stopped=True

    def update_gps(self):
        """
            Get the GPS position from the dragino,
            using gpsd

            updates the cached GPS values when a TPV message is seen
            this could mean the cached time is out of sync with reality
            so we also save a timestamp when the reading was valid

            Caller can compute actual time using the GPS timestamp and the
            time the reading was cached.

        """
        try:
            self.logger.info("update GPS")
            new_data = self.gpsd_socket.next()
            if new_data is not None:
                data = json.loads(new_data)
                thisClass=data["class"]
                self.logger.info(f"GPS new_data class {thisClass}")
                if thisClass == "TPV" and data["mode"] >1 :
                    self.lat = data["lat"]
                    self.lon = data["lon"]
                    self.timestamp = data["time"]
                    self.lastGpsReading = time()

                # cache the sentence
                data["lastGpsReading"] = time() # record when reading took place
                self.sentences[thisClass]=data

            else:
                self.logger.info("No new gps data")
        except Exception as e:
            self.logger.warning("update_gps() ignoring exception %s", e)

    def getSentence(self,which):
        """
        Returns the cached GPSD sentence or None

        This allows callers to access more than just the device lat/lon and time
        """
        try:
            return self.sentences[which]
        except Exception as e:
            self.logger.info(f"attempt to retrieve sentence {which} which doesn't exist")
            return None