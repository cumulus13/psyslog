import os
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, PyMongoError
from datetime import datetime
from rich.console import Console
from rich.text import Text

console = Console()

# Color mapping based on syslogseverity-text
SEVERITY_COLORS = {
    "emerg": "bold red",
    "alert": "bold red",
    "crit": "bold red",
    "err": "yellow",
    "warning": "yellow",
    "notice": "green",
    "info": "green",
    "debug": "blue",
}

def connect_to_mongo():
    """Connect to MongoDB using environment variables."""
    host = os.getenv("MONGO_HOST", "192.168.100.2")
    port = int(os.getenv("MONGO_PORT", 27017))
    username = os.getenv("MONGO_USER", "admin")
    password = os.getenv("MONGO_PASS", "admin")
    auth_db = os.getenv("MONGO_AUTH_DB", "admin")

    try:
        client = MongoClient(host=host, port=port, username=username, password=password, authSource=auth_db)
        console.print("[INFO] Connected to MongoDB", style="green")
        return client
    except ConnectionFailure as e:
        console.print(f"[ERROR] Connection failure: {e}", style="bold red")
    except PyMongoError as e:  # Catching general pymongo errors, including authentication issues
        console.print(f"[ERROR] MongoDB error: {e}", style="bold red")
    except Exception as e:
        console.print(f"[ERROR] Unexpected error: {e}", style="bold red")
    return None

def fetch_logs(client, last_time):
    """Fetch and print logs from MongoDB."""
    db = client["syslogdb"]
    collection = db["logs"]

    console.print(f"\n[INFO] Fetching logs at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", style="cyan")

    try:
        # Debug: Print last_time before query
        console.print(f"[DEBUG] last_time: {last_time}", style="magenta")

        query = {"timegenerated": {"$gt": last_time}} if last_time else {}
        logs = collection.find(query).sort("timegenerated", 1)

        log_list = list(logs)
        if len(log_list) == 0:
            console.print("[INFO] No new logs found.", style="yellow")
        else:
            console.print(f"[INFO] Found {len(log_list)} new logs.", style="green")

        new_last_time = last_time
        for log in log_list:
            severity = log.get("syslogseverity-text", "info").lower()
            color = SEVERITY_COLORS.get(severity, "white")

            log_msg = Text(f"[{log.get('timegenerated')}] {log.get('hostname')} - {log.get('msg')}", style=color)
            console.print(log_msg)

            # Debugging: Print raw log and type of `timegenerated`
            current_time = log.get("timegenerated")
            console.print(f"[DEBUG] Raw timegenerated: {current_time}, Type: {type(current_time)}", style="magenta")
            
            # If the time is a string, attempt to convert it to a datetime object
            if isinstance(current_time, str):
                try:
                    current_time = datetime.fromisoformat(current_time)
                    console.print(f"[DEBUG] Parsed timegenerated as datetime: {current_time}", style="magenta")
                except ValueError:
                    console.print(f"[ERROR] Invalid datetime format: {current_time}", style="bold red")
                    continue  # Skip this log if the datetime is invalid

            # Check and compare time
            if current_time and (new_last_time is None or current_time > new_last_time):
                console.print(f"[DEBUG] Updating new_last_time from {new_last_time} to {current_time}", style="magenta")
                new_last_time = current_time
            else:
                console.print(f"[DEBUG] Skipping log due to invalid or older timestamp", style="magenta")

        return new_last_time

    except Exception as e:
        console.print(f"[ERROR] Failed to fetch logs: {e}", style="bold red")
        return last_time

if __name__ == "__main__":
    client = connect_to_mongo()
    if client:
        last_time = None
        while True:
            last_time = fetch_logs(client, last_time)
            time.sleep(5)  # Wait 5 seconds before fetching logs again
    else:
        console.print("[ERROR] Exiting due to MongoDB connection failure.", style="bold red")
