
import json
from pathlib import Path

class RedemptionEngine:
    REDEEMED_USERS_PATH = Path("redeemed_users.json")

    @staticmethod
    def submit_redemption(identity: str, scroll_text: str, trust_node_signatures: list):
        if len(trust_node_signatures) < 3:
            raise PermissionError("⚠️ Not enough trusted node approvals.")

        entry = {
            "identity": identity,
            "scroll_text": scroll_text,
            "trust_node_signatures": trust_node_signatures
        }

        if RedemptionEngine.REDEEMED_USERS_PATH.exists():
            data = json.loads(RedemptionEngine.REDEEMED_USERS_PATH.read_text())
        else:
            data = []

        data.append(entry)
        RedemptionEngine.REDEEMED_USERS_PATH.write_text(json.dumps(data, indent=2))
        print(f"✅ Redemption submitted for {identity}")
