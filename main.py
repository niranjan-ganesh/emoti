import threading
import queue
import signal
import sys
from src.channel_manager import ChannelManager  # Module to load and parse channels.json
from src.sensor_streamer import EmotibitStreamer  # Your sensor streaming code (producer)
from src.data_processor import DataProcessor        # Module for channel-specific data processing

def main():
    # --- Step 1: Load Channel Configuration ---
    # Create a ChannelManager instance that reads the JSON configuration.
    config_path = 'config/channels.json'
    channel_manager = ChannelManager(config_path)
    channels = channel_manager.get_channels()  # Returns channel info (list/dict) for processing

    # --- Step 2: Setup Shared Data Queue ---
    # Create a thread-safe queue to buffer data from the sensor.
    data_queue = queue.Queue()

    # --- Step 3: Initialize Sensor Streaming (Producer) ---
    # Instantiate the sensor streamer. Assume that it can push data into the provided queue.
    streamer = EmotibitStreamer(ip_address='192.168.137.17', ip_port=3131)
    # Modify your EmotibitStreamer to support a data queue, e.g., by setting:
    # self.data_queue = data_queue
    streamer.data_queue = data_queue  # This is where raw sensor data will be enqueued

    # --- Step 4: Initialize Data Processor (Consumer) ---
    # Create a DataProcessor that knows about channel configurations and the shared data queue.
    processor = DataProcessor(data_queue, channels)

    # --- Step 5: Start Threads for Streaming and Processing ---
    # Start the sensor streamer in its own thread.
    streaming_thread = threading.Thread(target=streamer.start)
    streaming_thread.start()

    # Start the data processing (consumer) thread.
    processing_thread = threading.Thread(target=processor.start_processing)
    processing_thread.start()

    # --- Step 6: Setup Graceful Shutdown ---
    # Define a shutdown handler that stops both streamer and processor.
    def shutdown_handler(sig, frame):
        print("Shutting down gracefully...")
        streamer.stop()      # Stops the sensor streaming and closes the session.
        processor.stop()     # Signals the processor to finish processing.
        streaming_thread.join()
        processing_thread.join()
        sys.exit(0)

    # Listen for Ctrl+C (SIGINT) to trigger graceful shutdown.
    signal.signal(signal.SIGINT, shutdown_handler)

    # --- Step 7: Wait for Threads to Complete ---
    # In a long-running application, these threads will run until a shutdown signal is received.
    streaming_thread.join()
    processing_thread.join()

if __name__ == '__main__':
    main()
