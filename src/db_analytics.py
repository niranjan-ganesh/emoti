# src/db_analytics.py
import pymongo
import pandas as pd

class DBAnalytics:
    def __init__(self, mongo_uri="mongodb://localhost:27017", 
                 db_name="dumps", collection_name="preprocessed", 
                 channel_index=1, update_interval=1000):
        """
        Initialize DBAnalytics.

        Args:
            mongo_uri (str): URI to connect to MongoDB.
            db_name (str): Name of the database.
            collection_name (str): Name of the collection.
            channel_index (int): The channel to analyze.
            update_interval (int): Update interval (in ms) if needed.
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.channel_index = channel_index
        self.update_interval = update_interval
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

    def start(self):
        """
        Start the DBAnalytics component.
        Since this component is used for on-demand analysis,
        start() simply indicates readiness.
        """
        print("DBAnalytics component ready for analysis.")

    def stop(self):
        """
        Stop the DBAnalytics component.
        Here, we simply close the MongoDB client connection.
        """
        self.client.close()
        print("DBAnalytics stopped.")

    def query_latest_data(self, limit=100):
        """
        Query the latest data records from MongoDB, sorted by timestamp.

        Args:
            limit (int): Number of records to fetch.

        Returns:
            pd.DataFrame: DataFrame with the latest data.
        """
        cursor = self.collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
        data = list(cursor)
        if data:
            df = pd.DataFrame(data)
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values(by="timestamp")
            return df
        else:
            return pd.DataFrame()

    def compute_statistics(self):
        """
        Compute basic statistics for the specified channel.

        Returns:
            dict: A dictionary containing summary statistics.
        """
        df = self.query_latest_data(limit=100)
        if df.empty:
            return {}
        channel_key = str(self.channel_index)
        if channel_key in df.columns:
            return df[channel_key].describe().to_dict()
        else:
            return {}