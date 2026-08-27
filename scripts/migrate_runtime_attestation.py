"""Apply the runtime attestation schema migration."""

import os
from pathlib import Path

import psycopg
from control_plane_runtime import validate_sovereign_database_url


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT
    / "core"
    / "ops"
    / "migrations"
    / "004_runtime_attestation.sql"
)


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    validate_sovereign_database_url(database_url)
    raw = MIGRATION.read_text(encoding="utf-8")
    statements = [
        s.strip()
        for s in raw.split(";")
        if s.strip() and not s.strip().startswith("--")
    ]
    with psycopg.connect(database_url, autocommit=True) as connection:
        for statement in statements:
            connection.execute(statement)
        row = connection.execute(
            """SELECT current_database(), current_user,
                      COALESCE(inet_server_addr()::text, 'local_socket'),
                      inet_server_port()"""
        ).fetchone()
    print({
        "status": "migrated",
        "database": row[0],
        "user": row[1],
        "server": row[2],
        "port": row[3],
    })


if __name__ == "__main__":
    main()
