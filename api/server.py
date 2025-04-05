# api/server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from typing import Optional

app = FastAPI(title="BioSignal Data API")

# Setup MongoDB connection (adjust the URI as needed)
client = MongoClient("mongodb://localhost:27017")
db = client["dumps"]
data_collection = db["preprocessed"]

# Pydantic model to validate incoming data samples.
class DataSample(BaseModel):
    # We expect a dictionary of sensor readings, e.g.:
    # { "0": 23125.0, "1": -1.006, ... }
    sample: dict

@app.post("/push-data/", response_model=dict)
def push_data(data: DataSample):
    """
    Endpoint to push a new sensor data sample into MongoDB.
    """
    try:
        result = data_collection.insert_one(data.sample)
        return {"status": "success", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-data/", response_model=dict)
def get_data(limit: Optional[int] = 100):
    """
    Endpoint to retrieve stored sensor data.
    Optionally limit the number of records returned.
    """
    try:
        data = list(data_collection.find({}, {"_id": 0}).limit(limit))
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
