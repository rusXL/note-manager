import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
from pathlib import Path

import os
from dotenv import load_dotenv

load_dotenv()

# sql connection pool configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root"),
    "database": os.getenv("DB_NAME", "note_manager"),
}

# global switch: True = SQL (MariaDB), False = NoSQL (MongoDB)
_use_sql = True
_connection_pool = None


# should be run during migration or on initial run
def init_db():
    schema_sql = (Path(__file__).parent / "schema.sql").read_text()

    # use temporary connection
    conn = mysql.connector.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )

    with conn.cursor() as cur:
        cur.execute(schema_sql, map_results=True)
        for _ in cur.fetchsets():
            pass  # consume results
        conn.commit()

    conn.close()


# will not work on the initial run because db is not created
def init_db_pool():
    global _use_sql, _connection_pool

    if _use_sql:
        _connection_pool = pooling.MySQLConnectionPool(
            pool_name="note_manager_pool", pool_size=5, **DB_CONFIG
        )
    else:
        # TODO: mongo
        pass


def close_db_pool():
    global _use_sql, _connection_pool

    if _use_sql:
        _connection_pool = None
    else:
        # TODO: mongo
        pass


@contextmanager
def get_db():
    global _use_sql, _connection_pool

    if not _connection_pool:
        init_db_pool()

    if _use_sql:
        conn = _connection_pool.get_connection()
    else:
        # TODO: mongo
        pass

    try:
        yield conn
    finally:
        conn.close()


def toggle_db_mode():
    global _use_sql

    _use_sql = not _use_sql

    return get_db_mode()


def get_db_mode():
    global _use_sql

    return "sql" if _use_sql else "nosql"
