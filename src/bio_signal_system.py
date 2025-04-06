# src/biosignal_system.py
import queue
import time
from threading import Thread
from src.sensor_streamer import EmotibitStreamer
from src.data_storage import DataStorage
from src.transforms import DataTransforms
from src.db_analytics import DBAnalytics

class BiosignalSystem:
    """
    High-level API for biosignal data acquisition, storage, transforms,
    and analytics from the database.
    """
    def __init__(self, ip_address='192.168.137.17', ip_port=3131, 
                 channel_index=1, update_interval=1000, 
                 mongo_uri="mongodb://localhost:27017", db_name="dumps", 
                 collection_name="preprocessed"):
        # Create separate queues for storage, analytics, and transforms.
        self.storage_queue = queue.Queue()
        self.analytics_queue = queue.Queue()
        self.transform_queue = queue.Queue()

        # Initialize the sensor streamer with all queues.
        self.streamer = EmotibitStreamer(ip_address=ip_address, ip_port=ip_port,
                                         storage_queue=self.storage_queue,
                                         analytics_queue=self.analytics_queue,
                                         transform_queue=self.transform_queue)
        # Initialize consumer components.
        self.storage_consumer = DataStorage(storage_queue=self.storage_queue, 
                                            mongo_uri=mongo_uri,
                                            db_name=db_name,
                                            collection_name=collection_name)
        self.transforms_consumer = DataTransforms(transform_queue=self.transform_queue, 
                                                  channel_index=channel_index)
        # Use DBAnalytics to perform analytics by querying the database.
        self.db_analytics = DBAnalytics(mongo_uri=mongo_uri, db_name=db_name,
                                        collection_name=collection_name,
                                        channel_index=channel_index,
                                        update_interval=update_interval)
        self._components = [self.streamer, self.storage_consumer, self.transforms_consumer, self.db_analytics]
        self._running = False

    def start(self):
        """Start the biosignal system: acquisition, storage, transforms, and DB analytics."""
        self.streamer.start()
        self.transforms_consumer.start()
        self.storage_consumer.start()
        self.db_analytics.start()
        self._running = True
        print("Biosignal system started.")

    def stop(self):
        """Stop the biosignal system gracefully."""
        self.streamer.stop()
        self.transforms_consumer.stop()
        self.storage_consumer.stop()
        self.db_analytics.stop()
        self._running = False
        print("Biosignal system stopped.")

    def get_data(self):
        """Retrieve locally accumulated sensor data from the streamer."""
        return self.streamer.get_data()

    def is_running(self):
        """Return the current running state of the system."""
        return self._running

    def plot_live(self, channel_index=None, interval=None):
        """
        Delegate to the DB analytics consumer.
        You can update the channel_index and update_interval if desired.
        """
        if channel_index is not None:
            self.db_analytics.channel_index = channel_index
        if interval is not None:
            self.db_analytics.update_interval = interval
        print("Live plot (DB-based analytics) is active (parameters updated if provided).")