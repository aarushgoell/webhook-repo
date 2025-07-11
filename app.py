from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.json_util import dumps
from dotenv import load_dotenv
from flask_cors import CORS
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Connect to MongoDB
try:
    MONGO_URL = os.getenv("MONGO_URL")
    if not MONGO_URL:
        raise ValueError("MONGO_URL not set in environment")

    client = MongoClient(MONGO_URL)
    db = client["webhooks"]
    collection = db["events"]
    print("✅ MongoDB connected successfully")

except Exception as e:
    print("❌ MongoDB connection error:", str(e))
    collection = None

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Server started"})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        if collection is None:
            raise RuntimeError("MongoDB not connected")

        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        event_type = data.get("event", "unknown").lower()
        timestamp = data.get("timestamp", "unknown")
        author = data.get("author", "unknown")

        record = {
            "event": event_type,
            "author": author,
            "timestamp": timestamp
        }

        if event_type == "pull_request":
            record["from_branch"] = data.get("from_branch", "unknown")
            record["to_branch"] = data.get("to_branch", "unknown")

        elif event_type == "merge":
            record["from_branch"] = data.get("from_branch", "unknown")
            record["to_branch"] = data.get("to_branch", "unknown")

        elif event_type == "push":
            record["branch"] = data.get("branch", "unknown")

        collection.insert_one(record)
        print(f"✅ {event_type} event stored:", record)

        return jsonify({"message": f"{event_type} event stored successfully"}), 200

    except Exception as e:
        print("❌ Error in /webhook:", str(e))
        return jsonify({"error": "Webhook failed"}), 500

@app.route("/events", methods=["GET"])
def get_events():
    try:
        if collection is None:
            raise RuntimeError("MongoDB not connected")

        # Fetch only documents with valid timestamp
        events = list(collection.find({"timestamp": {"$exists": True}}).sort("timestamp", -1))
        print(f"✅ {len(events)} events fetched")
        return dumps(events), 200

    except Exception as e:
        print("❌ Error in /events:", str(e))
        return jsonify({"error": "Could not fetch events"}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
