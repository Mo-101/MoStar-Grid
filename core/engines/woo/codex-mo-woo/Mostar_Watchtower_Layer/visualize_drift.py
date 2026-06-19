
import json
import matplotlib.pyplot as plt
from pathlib import Path

def visualize_drift(identity: str, log_path="intent_shadow_log.json"):
    path = Path(log_path)
    if not path.exists():
        raise FileNotFoundError("Log file not found.")

    data = json.loads(path.read_text())
    user_data = [d for d in data if d["identity"] == identity]

    if not user_data:
        raise ValueError(f"No entries found for identity: {identity}")

    timestamps = [entry["timestamp"] for entry in user_data]
    entropies = [entry["entropy"] for entry in user_data]

    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, entropies, marker='o', linestyle='-', color='orange')
    plt.title(f"Entropy Drift for {identity}")
    plt.xlabel("Timestamp")
    plt.ylabel("Entropy Score")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid(True)
    plt.show()
