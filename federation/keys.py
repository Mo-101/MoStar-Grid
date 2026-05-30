"""Cluster public key registry for federation verification."""
from __future__ import annotations

import json
from pathlib import Path

from grid.config import PEER_KEYS_PATH


class UnknownClusterKeyError(KeyError):
    pass


class ClusterKeyRegistry:
    def __init__(self, path: Path | None = None, keys: dict[str, str] | None = None):
        self.path = path or PEER_KEYS_PATH
        self._keys = dict(keys or {})

    def get_public_key(self, cluster_id: str) -> str:
        keys = {**self._read_file(), **self._keys}
        try:
            return keys[cluster_id]
        except KeyError as exc:
            raise UnknownClusterKeyError(cluster_id) from exc

    def set_public_key(self, cluster_id: str, public_key: str) -> None:
        keys = self._read_file()
        keys[cluster_id] = public_key
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(keys, handle, ensure_ascii=False, sort_keys=True, indent=2)

    def _read_file(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        with open(self.path, "r", encoding="utf-8") as handle:
            return json.load(handle)
