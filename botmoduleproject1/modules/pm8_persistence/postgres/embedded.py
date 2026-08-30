"""Start a local PostgreSQL 16 binary in a user namespace (sandbox / CI helper).

Not used in production. Production supplies BOTMODULEPROJECT1_DATABASE_URL.
PostgreSQL refuses uid 0; this helper maps the process to uid 1000 via unshare.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

DEFAULT_PORT = 55432
DEFAULT_USER = "pm8"
DEFAULT_DB = "pm8_test"


def _pg_bin() -> Path:
    import pgserver

    return Path(pgserver.__file__).resolve().parent / "pginstall" / "bin"


def port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    sock = socket.socket()
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def dsn_for(port: int = DEFAULT_PORT, user: str = DEFAULT_USER, database: str = DEFAULT_DB) -> str:
    return f"postgresql://{user}@127.0.0.1:{port}/{database}"


def _unshare_cmd(inner: str, env: dict[str, str]) -> list[str]:
    export = " ".join(f"{k}={v}" for k, v in env.items())
    return ["unshare", "--user", "--map-user=1000", "--map-group=1000", "/bin/bash", "-c", f"export {export}; {inner}"]


def start_embedded_postgres(
    *,
    pgdata: Path | None = None,
    port: int = DEFAULT_PORT,
    user: str = DEFAULT_USER,
    database: str = DEFAULT_DB,
) -> str:
    """Idempotent: return DSN if already listening, otherwise init+start."""
    if port_open("127.0.0.1", port):
        return dsn_for(port, user, database)
    bin_dir = _pg_bin()
    postgres = bin_dir / "postgres"
    if not postgres.exists():
        raise RuntimeError(f"embedded postgres binary missing at {postgres}")
    data = pgdata or Path("/tmp/pm8-pg-real")
    run_dir = Path("/tmp/pm8-pgrun")
    data.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    env = {"PG_BIN": str(bin_dir), "PGDATA": str(data), "PORT": str(port)}
    if not (data / "PG_VERSION").exists():
        init = (
            f'"{bin_dir}/initdb" -D "{data}" --auth=trust --no-sync '
            f'--username={user} --encoding=UTF8 --locale=C'
        )
        subprocess.run(_unshare_cmd(init, env), check=True, capture_output=True, text=True)
        conf = data / "postgresql.conf"
        extra = (
            f"\nlisten_addresses = '127.0.0.1'\n"
            f"port = {port}\n"
            f"unix_socket_directories = '{run_dir}'\n"
            f"logging_collector = off\n"
            f"shared_buffers = 32MB\n"
            f"max_connections = 40\n"
            f"fsync = off\n"
            f"synchronous_commit = off\n"
            f"full_page_writes = off\n"
        )
        conf.write_text(conf.read_text(encoding="utf-8") + extra, encoding="utf-8")
    start = f'"{bin_dir}/pg_ctl" -D "{data}" -l /tmp/pm8-pg.log -w start'
    subprocess.run(_unshare_cmd(start, env), check=True, capture_output=True, text=True)
    deadline = time.time() + 15
    while time.time() < deadline:
        if port_open("127.0.0.1", port):
            break
        time.sleep(0.1)
    else:
        log = Path("/tmp/pm8-pg.log").read_text(encoding="utf-8") if Path("/tmp/pm8-pg.log").exists() else ""
        raise RuntimeError(f"embedded postgres did not start on {port}: {log[-1000:]}")
    psql = bin_dir / "psql"
    probe = [
        str(psql),
        "-h",
        "127.0.0.1",
        "-p",
        str(port),
        "-U",
        user,
        "-d",
        "postgres",
        "-tc",
        f"SELECT 1 FROM pg_database WHERE datname='{database}'",
    ]
    out = subprocess.run(probe, check=True, capture_output=True, text=True)
    if not out.stdout.strip():
        subprocess.run(
            [
                str(psql),
                "-h",
                "127.0.0.1",
                "-p",
                str(port),
                "-U",
                user,
                "-d",
                "postgres",
                "-c",
                f"CREATE DATABASE {database}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    return dsn_for(port, user, database)


def which_psql() -> str | None:
    found = shutil.which("psql")
    if found:
        return found
    candidate = _pg_bin() / "psql"
    return str(candidate) if candidate.exists() else None


def discover_dsn() -> str | None:
    env = os.environ.get("BOTMODULEPROJECT1_DATABASE_URL", "").strip()
    if env:
        return env
    if port_open("127.0.0.1", DEFAULT_PORT):
        return dsn_for()
    if port_open("127.0.0.1", 5432):
        return "postgresql://pm8@127.0.0.1:5432/pm8_test"
    return None
