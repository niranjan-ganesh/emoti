import threading
import pandas as pd
import queue
import biosignalsnotebooks as bsnb  # Ensure this package is installed and available

class DataTransforms:
    def __init__(self, transform_queue, channel_index):
        """
        Initializes the DataTransforms consumer.

        Args:
            transform_queue (queue.Queue): Queue from which data batches are received.
            channel_index (int): The key/index for the desired channel (e.g., 3).
        """
        self.transform_queue = transform_queue
        self.channel_index = channel_index  # now expected to be a number
        self.data = pd.DataFrame()  # Accumulate transformed data here.
        self.running = False
        self.thread = None

    def eda_preprocess(self, df):
        """
        Extracts a one-column DataFrame for the specified channel and applies EDA preprocessing.
        Specifically, it converts raw sensor values to physical units (uS) using the bsnb.raw_to_phy function.

        Args:
            df (pd.DataFrame): A DataFrame containing sensor data.

        Returns:
            pd.DataFrame: A new DataFrame with the transformed data.
        """
        col = self.channel_index  # assuming df columns are numbers
        if col not in df.columns:
            print(f"Column '{col}' not found. Available columns: {df.columns}")
            return pd.DataFrame()  # Return empty DataFrame if the column is missing.

        # Extract the desired column as a one-column DataFrame.
        one_column_df = df[[col]]
        # Get raw values as a numpy array.
        raw_values = one_column_df[col].values  
        # Convert raw sensor values to physical units (uS).
        # Adjust the parameters as needed: measurement type "EDA", sensor "bitalino_rev", scale factor 10, unit "uS".
        transformed_values = bsnb.raw_to_phy("EDA", "bitalino_rev", raw_values, 10, "uS")
        # Create a new DataFrame from the transformed values.
        transformed_df = pd.DataFrame(transformed_values, columns=[f"PRE{col}"])
        print("eda_preprocess:", transformed_df.head())
        return transformed_df

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
        print("Accumulated transformed data:")
        print(self.data)
        if not self.data.empty:
            self.data.to_csv("channel_processed.csv", index=False)
            print("Local data saved to 'channel_processed.csv'.")
        print("DataTransforms consumer stopped.")

    def _process_queue(self):
        """Continuously process data for transforms."""
        while self.running:
            try:
                data_batch = self.transform_queue.get(timeout=1)
                print("Received batch with shape:", data_batch.shape)
                transformed_df = self.eda_preprocess(data_batch)
                self.data = pd.concat([self.data, transformed_df], ignore_index=True)
                self.transform_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print("Error in DataTransforms consumer:", e)