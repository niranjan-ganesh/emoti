import threading
import time
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class RealTimeAnalytics:
    def __init__(self, analytics_queue, channel_index=1, update_interval=1000):
        self.analytics_queue = analytics_queue
        self.channel_index = channel_index
        self.update_interval = update_interval  # milliseconds
        self.running = False
        self.thread = None
        self.data = pd.DataFrame()  # Accumulate for analytics
        self.fig, self.ax = plt.subplots()
        self.ani = None

    def start(self):
        """Start the analytics consumer thread and live plotting."""
        self.running = True
        self.thread = threading.Thread(target=self._process_queue)
        self.thread.start()
        # Start live plotting via FuncAnimation
        self.ani = FuncAnimation(self.fig, self._update_plot, interval=self.update_interval)
        plt.show(block=False)
        print("RealTimeAnalytics consumer started.")

    def _process_queue(self):
        """Continuously process data for analytics."""
        while self.running:
            try:
                data_batch = self.analytics_queue.get(timeout=1)
                # Append new data to the analytics DataFrame
                self.data = pd.concat([self.data, data_batch], ignore_index=True)
                self.analytics_queue.task_done()
            except Exception as e:
                # Timeout or empty queue; continue loop
                continue

    def _update_plot(self, frame):
        """Update live plot for the specified channel."""
        if not self.data.empty:
            self.ax.clear()
            self.ax.plot(self.data.index, self.data[self.channel_index], label=f"Channel {self.channel_index}")
            self.ax.set_title("Real-Time Sensor Data")
            self.ax.set_xlabel("Sample Index")
            self.ax.set_ylabel("Sensor Value")
            self.ax.legend()

    def stop(self):
        """Stop the analytics consumer thread."""
        self.running = False
        if self.thread is not None:
            self.thread.join()
        print("RealTimeAnalytics consumer stopped.")
