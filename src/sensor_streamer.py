import time
import threading
import pandas as pd
from brainflow.board_shim import BrainFlowInputParams, BoardShim, BoardIds

class EmotibitStreamer:
    def __init__(self, ip_address='192.168.137.17', ip_port=3131, 
                 storage_queue=None, analytics_queue=None, transform_queue=None):
        # Initialize BrainFlow parameters and board
        self.params = BrainFlowInputParams()
        self.params.ip_address = ip_address
        self.params.ip_port = ip_port
        self.board_id = BoardIds.EMOTIBIT_BOARD.value
        self.board = BoardShim(self.board_id, self.params)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.fetch_interval = 1 / self.sampling_rate

        # Threading and local data storage
        self.streaming = False
        self.data_lock = threading.Lock()
        self.data = pd.DataFrame()
        self.thread = None

        # Queues for decoupled consumers
        self.storage_queue = storage_queue
        self.analytics_queue = analytics_queue
        self.transform_queue = transform_queue

    def start(self):
        """Prepare session and start the data streaming thread."""
        self.board.prepare_session()
        self.board.start_stream()
        self.streaming = True
        self.thread = threading.Thread(target=self._stream_data)
        self.thread.start()
        print(f"Streaming started at {self.sampling_rate} Hz...")

    def _stream_data(self):
        """Continuously fetch data and push copies to both queues."""
        last_time = time.time()
        try:
            while self.streaming:
                board_data = self.board.get_board_data()
                if board_data.shape[1] > 0:
                    # Transpose data to have shape (samples, channels)
                    temp_df = pd.DataFrame(board_data.T)
                    
                    # Thread-safe concatenation of new data locally
                    with self.data_lock:
                        self.data = pd.concat([self.data, temp_df], ignore_index=True)
                    
                    # Get the latest sample for logging
                    latest_sample = temp_df.tail(1).to_dict(orient='records')[0]
                    print(f"Latest data sample: {latest_sample}")
                    
                    # Push a copy to the storage queue
                    if self.storage_queue is not None:
                        self.storage_queue.put(temp_df.copy())
                    
                    # Push a copy to the analytics queue
                    if self.analytics_queue is not None:
                        self.analytics_queue.put(temp_df.copy())
                    
                    if self.transform_queue is not None:
                        self.transform_queue.put(temp_df.copy())
                
                # Adjust sleep time based on sampling rate
                elapsed_time = time.time() - last_time
                sleep_time = max(self.fetch_interval - elapsed_time, 0)
                time.sleep(sleep_time)
                last_time = time.time()
        except Exception as e:
            print(f"Error during streaming: {e}")
        finally:
            self.board.stop_stream()
            self.board.release_session()
            print("Session closed.")

    def stop(self):
        """Stop the streaming thread and optionally save local data to CSV."""
        self.streaming = False
        if self.thread is not None:
            self.thread.join()
        # Save local data as backup if desired
        if not self.data.empty:
            self.data.to_csv("emotibit_data.csv", index=False)
            print("Local data saved to 'emotibit_data.csv'.")

    def get_data(self):
        """Return a copy of the locally accumulated data."""
        with self.data_lock:
            return self.data.copy()
