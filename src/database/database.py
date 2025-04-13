import logging
import os

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


def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding("UTF8")
    return conn


class DatabaseService:
    def __init__(self) -> None:
        self.conn = get_db_connection()
        self.cur = self.conn.cursor()

    def __enter__(self):
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.debug("Closing database connection")
        if self.conn:
            self.conn.close()
        if self.cur:
            self.cur.close()
