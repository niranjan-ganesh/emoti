import time

class DataProcessor:
    def __init__(self, data_queue, channels):
        """
        Initialize the DataProcessor.
        
        Args:
            data_queue: Shared queue where sensor data is stored.
            channels: Parsed channel configuration from ChannelManager.
        """
        self.data_queue = data_queue
        self.channels = channels
        self.processing = False

    def start_processing(self):
        """
        Start processing data from the queue. This method runs in its own thread.
        """
        self.processing = True
        while self.processing:
            try:
                # Wait for new data (with a timeout to allow checking the processing flag)
                data = self.data_queue.get(timeout=1)
                # Process data according to channel configuration
                self.process_data(data)
                self.data_queue.task_done()
            except Exception:
                # Timeout or empty queue; continue the loop
                continue

    def process_data(self, data):
        """
        Process a batch of data.
        
        This method should include the logic to handle different channels based on their
        operating frequency and other properties. For simplicity, this example prints the
        latest sample.
        
        Args:
            data: A pandas DataFrame containing a batch of sensor data.
        """
        # Example processing: print the latest sample for monitoring
        latest_sample = data.tail(1).to_dict(orient='records')[0]
        print("Processed Data Sample:", latest_sample)
        # You can extend this method to perform channel-specific tasks based on self.channels

    def stop(self):
        """
        Stop the data processing loop.
        """
        self.processing = False
