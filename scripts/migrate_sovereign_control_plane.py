"""Apply the idempotent local Postgres governance schema migration."""

from pathlib import Path
import os

import psycopg

from control_plane_runtime import validate_sovereign_database_url


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "core" / "ops" / "migrations" / "001_sovereign_governance.sql"


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    validate_sovereign_database_url(database_url)
    sql = MIGRATION.read_text(encoding="utf-8")
    with psycopg.connect(database_url, autocommit=True) as connection:
        connection.execute(sql)
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
