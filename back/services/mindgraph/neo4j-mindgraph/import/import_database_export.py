import argparse
import ast
import csv
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from neo4j import GraphDatabase

BACKEND_DIR = Path(__file__).resolve().parents[2]
EXPORT_BASE_DIR = Path(__file__).resolve().parent / "database_export"
ENV_PATH = BACKEND_DIR / ".env"
EMPTY_VALUES = {"", "nan", "null", "none", "nil", "n/a"}
GENERIC_LABELS = {
    "MindLayer",
    "BodyLayer",
    "SoulLayer",
    "ConsciousnessLayer",
    "KnowledgeDomain",
}
IDENTITY_RULES = {
    "MoStarMoment": [("fingerprint",), ("quantum_id",), ("id",)],
    "Agent": [("agent_id",), ("id",), ("name",)],
    "Task": [("task_id",), ("id",)],
    "Metric": [("metric_id",), ("id",)],
    "Event": [("event_id",), ("id",)],
    "ExecutionEvent": [("event_id",), ("id",)],
    "Entity": [("entity_id",), ("id",), ("name",)],
    "APIEndpoint": [("endpoint_id",), ("route",), ("id",)],
    "IbibioIntegration": [("integration_id",), ("component",), ("id",)],
    "IbibioWord": [("word",), ("orthography",), ("id",)],
    "OduIfa": [("odu_number",), ("binary_pattern",), ("id",)],
    "Philosophy": [("name",), ("id",)],
    "Plant": [("scientific_name",), ("name",), ("id",)],
    "Proverb": [("proverb_or_wisdom",), ("text",), ("id",)],
    "Language": [("language",), ("iso_code",), ("id",)],
    "Region": [("region",), ("name",), ("id",)],
    "Governance": [("name",), ("id",)],
    "HealingPractice": [("name",), ("id",)],
    "KnowledgeGraphTriple": [("subject", "predicate", "object"), ("id",)],
    "MoScript": [("id",), ("name",)],
}


def resolve_neo4j_config() -> dict[str, str]:
    env_values = dotenv_values(ENV_PATH)
    return {
        "uri": env_values.get("NEO4J_URI")
        or os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": env_values.get("NEO4J_USER") or os.getenv("NEO4J_USER", "neo4j"),
        "password": env_values.get("NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD", ""),
    }


def normalize_datetime(value: str) -> Any:
    if not re.match(r"^\d{4}-\d{2}-\d{2}T", value):
        return value
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"
    match = re.match(r"^(.*?)(?:\.(\d+))?([+-]\d{2}:\d{2})$", candidate)
    if not match:
        return value
    prefix, fraction, offset = match.groups()
    if fraction:
        fraction = fraction[:6].ljust(6, "0")
        candidate = f"{prefix}.{fraction}{offset}"
    else:
        candidate = f"{prefix}{offset}"
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        return value


def normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float, bool, list, dict, datetime)):
        return value
    text = str(value).strip()
    if not text:
        return None
    if text.lower() in EMPTY_VALUES:
        return None
    if text == "True":
        return True
    if text == "False":
        return False
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                return [item for item in parsed]
        except (ValueError, SyntaxError):
            pass
    if text.startswith("{") and text.endswith("}"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, dict):
                return parsed
        except (ValueError, SyntaxError):
            pass
    if re.fullmatch(r"-?\d+", text):
        try:
            return int(text)
        except ValueError:
            return text
    if re.fullmatch(r"-?\d+\.\d+", text):
        try:
            return float(text)
        except ValueError:
            return text
    if re.match(r"^\d{4}-\d{2}-\d{2}T", text):
        return normalize_datetime(text)
    return text


def sanitize_label(label: str) -> str | None:
    candidate = (label or "").strip()
    if not candidate:
        return None
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", candidate):
        return None
    return candidate


def parse_labels(value: str) -> list[str]:
    labels: list[str] = []
    for raw in (value or "").split(":"):
        label = sanitize_label(raw)
        if label and label not in labels:
            labels.append(label)
    return labels


def choose_primary_label(labels: list[str]) -> str:
    specific = [label for label in labels if label not in GENERIC_LABELS]
    if specific:
        return specific[-1]
    if labels:
        return labels[0]
    return "ImportedNode"


def resolve_merge_props(primary_label: str, row: dict[str, str]) -> dict[str, Any]:
    for candidate in IDENTITY_RULES.get(primary_label, [("id",)]):
        merge_props: dict[str, Any] = {}
        valid = True
        for field in candidate:
            value = normalize_value(row.get(field))
            if value is None:
                valid = False
                break
            merge_props[field] = value
        if valid:
            return merge_props
    export_id = normalize_value(row.get("id"))
    if export_id is None:
        raise ValueError(
            f"Node row is missing a usable identifier for label {primary_label}"
        )
    return {"export_id": export_id}


def merge_signature(
    primary_label: str, merge_props: dict[str, Any]
) -> tuple[str, tuple[tuple[str, str], ...]]:
    return (
        primary_label,
        tuple((key, repr(value)) for key, value in sorted(merge_props.items())),
    )


def build_node_props(row: dict[str, str], snapshot_tag: str) -> dict[str, Any]:
    props: dict[str, Any] = {
        "export_id": normalize_value(row.get("id")),
        "export_labels": row.get("labels", ""),
        "source_export_snapshot": snapshot_tag,
    }
    for key, raw_value in row.items():
        if key in {"id", "labels"}:
            continue
        value = normalize_value(raw_value)
        if value is not None:
            props[key] = value
    return props


def build_relationship_props(row: dict[str, str], snapshot_tag: str) -> dict[str, Any]:
    props: dict[str, Any] = {"source_export_snapshot": snapshot_tag}
    for key, raw_value in row.items():
        if key in {"from_id", "to_id", "rel_type"}:
            continue
        value = normalize_value(raw_value)
        if value is not None:
            props[key] = value
    return props


def chunked(items: list[dict[str, Any]], size: int):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def discover_snapshot(
    export_dir: Path, timestamp: str | None
) -> tuple[str, Path, Path]:
    if timestamp:
        nodes_path = export_dir / f"all_nodes_{timestamp}.csv"
        rels_path = export_dir / f"all_relationships_{timestamp}.csv"
        if not nodes_path.exists() or not rels_path.exists():
            raise FileNotFoundError(
                f"Snapshot {timestamp} not found under {export_dir}"
            )
        return timestamp, nodes_path, rels_path
    candidates = sorted(export_dir.glob("all_nodes_*.csv"))
    if not candidates:
        raise FileNotFoundError(f"No all_nodes_*.csv export found under {export_dir}")
    nodes_path = candidates[-1]
    discovered_timestamp = nodes_path.stem.replace("all_nodes_", "")
    rels_path = export_dir / f"all_relationships_{discovered_timestamp}.csv"
    if not rels_path.exists():
        raise FileNotFoundError(
            f"Matching relationship export missing for {discovered_timestamp}"
        )
    return discovered_timestamp, nodes_path, rels_path


def load_nodes(
    nodes_path: Path, snapshot_tag: str
) -> tuple[
    dict[tuple[str, tuple[str, ...], tuple[str, ...]], list[dict[str, Any]]],
    Counter,
    int,
    dict[Any, Any],
]:
    grouped: dict[
        tuple[str, tuple[str, ...], tuple[str, ...]], list[dict[str, Any]]
    ] = defaultdict(list)
    prepared_rows: list[dict[str, Any]] = []
    merge_signature_counts: Counter = Counter()
    seen_export_ids: set[Any] = set()
    stats = Counter()
    with nodes_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            stats["node_rows_seen"] += 1
            export_id = normalize_value(row.get("id"))
            if export_id in seen_export_ids:
                stats["duplicate_node_rows_skipped"] += 1
                continue
            seen_export_ids.add(export_id)
            labels = parse_labels(row.get("labels", ""))
            primary_label = choose_primary_label(labels)
            merge_props = resolve_merge_props(primary_label, row)
            props = build_node_props(row, snapshot_tag)
            merge_signature_counts[merge_signature(primary_label, merge_props)] += 1
            prepared_rows.append(
                {
                    "primary_label": primary_label,
                    "labels": labels,
                    "merge_props": merge_props,
                    "props": props,
                }
            )
            stats["node_rows_loaded"] += 1
            stats[f"node_label::{primary_label}"] += 1
    collision_signatures = {
        signature
        for signature, count in merge_signature_counts.items()
        if count > 1
        and not (len(signature[1]) == 1 and signature[1][0][0] == "export_id")
    }
    canonical_export_ids: dict[tuple[str, tuple[tuple[str, str], ...]], Any] = {}
    export_id_aliases: dict[Any, Any] = {}
    stats["merge_key_collision_groups"] = len(collision_signatures)
    for prepared in prepared_rows:
        primary_label = prepared["primary_label"]
        labels = prepared["labels"]
        merge_props = prepared["merge_props"]
        props = prepared["props"]
        signature = merge_signature(primary_label, merge_props)
        canonical_export_id = canonical_export_ids.setdefault(
            signature, props["export_id"]
        )
        export_id_aliases[props["export_id"]] = canonical_export_id
        if signature in collision_signatures:
            stats["merge_key_collision_rows"] += 1
            stats[f"merge_key_collision_label::{primary_label}"] += 1
        merged_props = dict(props)
        merged_props["export_id"] = canonical_export_id
        all_labels = [primary_label] + [
            label for label in labels if label != primary_label
        ]
        key = (primary_label, tuple(all_labels), tuple(sorted(merge_props.keys())))
        grouped[key].append({"merge": merge_props, "props": merged_props})
    return grouped, stats, len(set(export_id_aliases.values())), export_id_aliases


def load_relationships(
    rels_path: Path, snapshot_tag: str, export_id_aliases: dict[Any, Any]
) -> tuple[dict[str, list[dict[str, Any]]], Counter]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    stats = Counter()
    with rels_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            stats["relationship_rows_seen"] += 1
            rel_type = sanitize_label(row.get("rel_type", ""))
            raw_from_id = normalize_value(row.get("from_id"))
            raw_to_id = normalize_value(row.get("to_id"))
            from_id = export_id_aliases.get(raw_from_id)
            to_id = export_id_aliases.get(raw_to_id)
            if not rel_type or from_id is None or to_id is None:
                stats["relationship_rows_skipped"] += 1
                continue
            grouped[rel_type].append(
                {
                    "from_id": from_id,
                    "to_id": to_id,
                    "props": build_relationship_props(row, snapshot_tag),
                }
            )
            stats["relationship_rows_loaded"] += 1
            stats[f"relationship_type::{rel_type}"] += 1
    return grouped, stats


def create_supporting_constraint(driver) -> None:
    # Constraint disabled during import - create manually after if needed
    # The MERGE pattern now includes export_id for uniqueness
    pass


def merge_node_batches(
    driver,
    grouped_nodes: dict[
        tuple[str, tuple[str, ...], tuple[str, ...]], list[dict[str, Any]]
    ],
    batch_size: int,
) -> Counter:
    stats = Counter()
    with driver.session() as session:
        for (primary_label, all_labels, merge_keys), rows in grouped_nodes.items():
            label_set = ["ImportedSnapshot"] + [
                label for label in all_labels if label != primary_label
            ]
            # Include export_id in merge pattern to prevent constraint violations
            merge_pattern = ", ".join(f"{key}: row.merge.{key}" for key in merge_keys)
            merge_pattern += ", export_id: row.props.export_id"
            set_labels = "".join(f":{label}" for label in label_set)
            query = (
                f"UNWIND $rows AS row "
                f"MERGE (n:{primary_label} {{{merge_pattern}}}) "
                f"SET n{set_labels} "
                f"SET n += row.props"
            )
            for batch in chunked(rows, batch_size):
                session.run(query, rows=batch).consume()
                stats["node_batches_executed"] += 1
                stats["nodes_merged_or_updated"] += len(batch)
                stats[f"node_merge_group::{primary_label}"] += len(batch)
    return stats


def merge_relationship_batches(
    driver, grouped_relationships: dict[str, list[dict[str, Any]]], batch_size: int
) -> Counter:
    stats = Counter()
    with driver.session() as session:
        for rel_type, rows in grouped_relationships.items():
            query = (
                "UNWIND $rows AS row "
                "MATCH (source:ImportedSnapshot {export_id: row.from_id}) "
                "MATCH (target:ImportedSnapshot {export_id: row.to_id}) "
                f"MERGE (source)-[r:{rel_type}]->(target) "
                "SET r += row.props"
            )
            for batch in chunked(rows, batch_size):
                session.run(query, rows=batch).consume()
                stats["relationship_batches_executed"] += 1
                stats["relationships_merged_or_updated"] += len(batch)
                stats[f"relationship_merge_group::{rel_type}"] += len(batch)
    return stats


def snapshot_totals(driver, snapshot_tag: str) -> dict[str, int]:
    node_query = (
        "MATCH (n:ImportedSnapshot {source_export_snapshot: $snapshot_tag}) "
        "RETURN count(n) AS count"
    )
    relationship_query = (
        "MATCH ()-[r]->() WHERE r.source_export_snapshot = $snapshot_tag "
        "RETURN count(r) AS count"
    )
    with driver.session() as session:
        node_count = session.run(node_query, snapshot_tag=snapshot_tag).single()[
            "count"
        ]
        relationship_count = session.run(
            relationship_query, snapshot_tag=snapshot_tag
        ).single()["count"]
    return {
        "snapshot_nodes": int(node_count or 0),
        "snapshot_relationships": int(relationship_count or 0),
    }


def print_stats(title: str, stats: Counter) -> None:
    print(title)
    for key in sorted(stats):
        if key.startswith("node_label::") or key.startswith("relationship_type::"):
            continue
        print(f"  {key}: {stats[key]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timestamp", default=None)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--relationships-batch-size", type=int, default=2000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = resolve_neo4j_config()
    if not config["password"]:
        raise SystemExit(
            "NEO4J_PASSWORD is not configured. Set it in backend/.env or environment variables."
        )

    snapshot_tag, nodes_path, rels_path = discover_snapshot(
        EXPORT_BASE_DIR, args.timestamp
    )
    print(f"snapshot_tag={snapshot_tag}")
    print(f"nodes_path={nodes_path}")
    print(f"relationships_path={rels_path}")

    grouped_nodes, node_load_stats, canonical_export_ids, export_id_aliases = (
        load_nodes(nodes_path, snapshot_tag)
    )
    grouped_relationships, relationship_load_stats = load_relationships(
        rels_path, snapshot_tag, export_id_aliases
    )
    print_stats("node_load_stats", node_load_stats)
    print_stats("relationship_load_stats", relationship_load_stats)
    print(f"canonical_export_ids={canonical_export_ids}")
    print(f"node_groups={len(grouped_nodes)}")
    print(f"relationship_groups={len(grouped_relationships)}")

    if args.dry_run:
        return

    driver = GraphDatabase.driver(
        config["uri"], auth=(config["user"], config["password"])
    )
    try:
        create_supporting_constraint(driver)
        node_merge_stats = merge_node_batches(driver, grouped_nodes, args.batch_size)
        relationship_merge_stats = merge_relationship_batches(
            driver, grouped_relationships, args.relationships_batch_size
        )
        totals = snapshot_totals(driver, snapshot_tag)
        print_stats("node_merge_stats", node_merge_stats)
        print_stats("relationship_merge_stats", relationship_merge_stats)
        print(f"snapshot_nodes={totals['snapshot_nodes']}")
        print(f"snapshot_relationships={totals['snapshot_relationships']}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
