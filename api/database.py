import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
from pathlib import Path

import os
import pymongo
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

MONGO_CONFIG = {
    "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
    "timeout": int(os.getenv("MONGO_TIMEOUT", 5000)),
    "database": os.getenv("MONGO_DB_NAME", "note_manager"),
}

# global switch: True = SQL (MariaDB), False = NoSQL (MongoDB)
_use_sql = True
_connection_pool = None
_mongo_client = None


# should be run during migration or on initial run
def init_db():
    global _use_sql
    if _use_sql:
        _init_sql_db()
    else:
        _init_mongo_db()


def _init_sql_db():
    """Initialize SQL (MariaDB) database schema."""
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


def _init_mongo_db():
    """Initialize MongoDB database (drops existing collections)."""
    client = pymongo.MongoClient(
        MONGO_CONFIG["uri"], serverSelectionTimeoutMS=MONGO_CONFIG["timeout"]
    )
    db = client[MONGO_CONFIG["database"]]

    # Drop existing collections for clean init
    db.users.drop()
    db.folders.drop()
    db.notes.drop()

    # Create indexes for efficient note filtering
    # Index on folder_id for folder-based queries
    db.notes.create_index("folder_id")
    # Compound index for filtering by folder + priority
    db.notes.create_index([("folder_id", 1), ("priority", 1)])
    # Compound index for filtering by folder + image existence
    db.notes.create_index([("folder_id", 1), ("image", 1)])

    client.close()


# will not work on the initial run because db is not created
def init_db_pool():
    global _use_sql, _connection_pool, _mongo_client

    if _use_sql:
        _connection_pool = pooling.MySQLConnectionPool(
            pool_name="note_manager_pool", pool_size=5, autocommit=True, **DB_CONFIG
        )
    else:
        _mongo_client = pymongo.MongoClient(
            MONGO_CONFIG["uri"], serverSelectionTimeoutMS=MONGO_CONFIG["timeout"]
        )


def close_db_pool():
    global _use_sql, _connection_pool, _mongo_client

    if _use_sql:
        _connection_pool = None
    else:
        if _mongo_client:
            _mongo_client.close()
            _mongo_client = None


@contextmanager
def get_db():
    global _use_sql, _connection_pool, _mongo_client

    if _use_sql:
        if not _connection_pool:
            init_db_pool()
        conn = _connection_pool.get_connection()
        try:
            yield conn
        finally:
            conn.close()
    else:
        if not _mongo_client:
            init_db_pool()
        # yield the database object
        db = _mongo_client[MONGO_CONFIG["database"]]
        yield db
        # no explicit close needed for mongo db object or client here


def toggle_db_mode():
    global _use_sql

    _use_sql = not _use_sql

    return get_db_mode()


def get_db_mode():
    global _use_sql

    return "sql" if _use_sql else "nosql"


def is_sql_mode():
    """Helper to check if currently in SQL mode."""
    global _use_sql
    return _use_sql
