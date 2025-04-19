import logging
import os
from typing import Literal

import psycopg2
from dotenv import load_dotenv

load_dotenv()


DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432"),
}


type SchemaType = Literal["public", "new_data"]


def get_db_connection(schema: SchemaType = "public") -> psycopg2.extensions.connection:
    conn = psycopg2.connect(**DB_CONFIG, options=f"-c search_path={schema}")
    conn.set_client_encoding("UTF8")
    return conn


class DatabaseService:
    def __init__(self, schema: SchemaType = "public") -> None:
        self.schema: SchemaType = schema
        self.conn: psycopg2.extensions.connection | None = None
        self.cur: psycopg2.extensions.cursor | None = None

    def __enter__(self) -> psycopg2.extensions.cursor:
        self.conn = get_db_connection(self.schema)
        self.cur = self.conn.cursor()
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.debug("Closing database connection")
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
