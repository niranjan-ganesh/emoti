import threading
import pandas as pd
import queue

class DataTransforms:
    def __init__(self, transform_queue, channel_index):
        self.transform_queue = transform_queue
        self.channel_index = channel_index
        self.data = pd.DataFrame()
        self.running = False
        self.thread = None

    def addtwo(self, df):
        """
        Extracts a one-column DataFrame for the specified channel and adds 2.
        """
        # Use double square brackets to ensure the result is a DataFrame.
        one_column_df = df[[self.channel_index]]
        transformed = one_column_df + 2
        print("transform:",transformed)
        return transformed

    def start(self):
        """Start the transforms consumer thread."""
        self.running = True
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
        print("DataTransforms consumer started.")

    def stop(self):
        """Stop the transforms consumer thread and save processed data to CSV."""
        self.running = False
        if self.thread is not None:
            self.thread.join()
        print("data,",self.data)
        if not self.data.empty:
            self.data.to_csv("channel_processed.csv", index=False)
            print("Local data saved to 'channel_processed.csv'.")
        print("DataTransforms consumer stopped.")

    def _process_queue(self):
        """Continuously process data for transforms."""
        while self.running:
            try:
                data_batch = self.transform_queue.get(timeout=1)
                # Process the data: extract one column and add 2.
                transformed_df = self.addtwo(data_batch)
                # Append the transformed data to our accumulated DataFrame.
                self.data = pd.concat([self.data, transformed_df], ignore_index=True)
                self.transform_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print("Error in DataTransforms consumer:", e)
