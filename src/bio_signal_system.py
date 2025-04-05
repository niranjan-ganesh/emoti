# src/biosignal_system.py
import queue
import time
from threading import Thread
from src.sensor_streamer import EmotibitStreamer
from src.data_storage import DataStorage
from src.analytics import RealTimeAnalytics
from src.transforms import DataTransforms

class BiosignalSystem:
    """
    High-level API for biosignal data acquisition and real-time analytics.
    
    This class abstracts away threading and queue management. Users can
    simply start or stop the system and interact with the data through provided
    methods.
    """
    def __init__(self, ip_address='192.168.137.17', ip_port=3131, 
                 channel_index=1, update_interval=100, 
                 mongo_uri="mongodb://localhost:27017", db_name="dumps", 
                 collection_name="preprocessed"):
        # Create separate queues for storage and analytics
        self.storage_queue = queue.Queue()
        self.analytics_queue = queue.Queue()
        self.transform_queue = queue.Queue()

        # Initialize the sensor streamer with both queues
        self.streamer = EmotibitStreamer(ip_address=ip_address, ip_port=ip_port,
                                         storage_queue=self.storage_queue,
                                         analytics_queue=self.analytics_queue,transform_queue=self.transform_queue)

        # Initialize consumer components
        self.storage_consumer = DataStorage(storage_queue=self.storage_queue, 
                                            mongo_uri=mongo_uri,
                                            db_name=db_name,
                                            collection_name=collection_name)
        self.analytics_consumer = RealTimeAnalytics(analytics_queue=self.analytics_queue, 
                                                    channel_index=channel_index, 
                                                    update_interval=update_interval)
        
        self.transforms_consumer = DataTransforms(transform_queue=self.transform_queue, channel_index=channel_index)
        self._components = [self.streamer, self.storage_consumer, self.analytics_consumer]
        self._running = False

    def start(self):
        """
        Start the biosignal system—begin data acquisition, storage, and analytics.
        """
        # Start each component in its own thread
        self.streamer.start()
        self.transforms_consumer.start()
        self.storage_consumer.start()
        self.analytics_consumer.start()

        self._running = True
        print("Biosignal system started.")

    def stop(self):
        """
        Stop the biosignal system gracefully.
        """
        self.streamer.stop()
        self.transforms_consumer.stop()
        self.storage_consumer.stop()
        self.analytics_consumer.stop()
        self._running = False
        print("Biosignal system stopped.")

    def get_data(self):
        """
        Retrieve locally accumulated sensor data from the streamer.
        """
        return self.streamer.get_data()

    def is_running(self):
        """
        Return the current running state of the system.
        """
        return self._running

    def plot_live(self, channel_index=None, interval=None):
        """
        Delegate to the analytics consumer's live plotting.
        You can update the channel_index and update_interval if desired.
        """
        if channel_index is not None:
            self.analytics_consumer.channel_index = channel_index
        if interval is not None:
            self.analytics_consumer.update_interval = interval
        # If the live plot is not already running, you might need to restart it.
        # In our design, the analytics consumer starts live plotting in its start() method.
        # Here we simply print a message and assume the live plot is already active.
        print("Live plot is active (parameters updated if provided).")
