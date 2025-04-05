import threading
import time
from pymongo import MongoClient
import queue  # For catching queue.Empty
from datetime import datetime

def convert_record_keys(record):
    """
    Recursively convert all keys in the dictionary to strings.
    """
    new_record = {}
    for key, value in record.items():
        # If the value is a dictionary, recursively convert its keys too.
        if isinstance(value, dict):
            value = convert_record_keys(value)
        new_record[str(key)] = value
    return new_record

class DataStorage:
    def __init__(self, storage_queue, mongo_uri="mongodb://localhost:27017", 
                 db_name="dumps", collection_name="preprocessed"):
        self.storage_queue = storage_queue
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[db_name]
        self.collection = self.db[collection_name]
        self.running = False
        self.thread = None

    def start(self):
        """Start the data storage consumer thread."""
        self.running = True
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
        print("DataStorage consumer started.")

    def _process_queue(self):
        """Continuously process and store incoming data."""
        while self.running:
            try:
                # Wait for data; timeout after 1 second to allow checking running flag.
                data_batch = self.storage_queue.get(timeout=1)
                # Convert DataFrame to list of dictionaries.
                records = data_batch.to_dict(orient="records")
                if records:
                    converted_records = []
                    for record in records:
                        # Convert keys to strings recursively.
                        new_record = convert_record_keys(record)
                        # Add a timestamp with the current UTC time in ISO format.
                        new_record["timestamp"] = datetime.utcnow().isoformat()
                        converted_records.append(new_record)
                    # Insert the converted records into MongoDB.
                    result = self.collection.insert_many(converted_records)
                    print(f"Inserted {len(result.inserted_ids)} records into MongoDB.")
                self.storage_queue.task_done()
            except queue.Empty:
                # No data available within the timeout, continue looping.
                continue
            except Exception as e:
                print("Error in DataStorage consumer:", e)

    def stop(self):
        """Stop the data storage consumer thread."""
        self.running = False
        if self.thread is not None:
            self.thread.join()
        print("DataStorage consumer stopped.")
