import os
import psycopg2

def get_connection():
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        return psycopg2.connect(database_url, sslmode="require")
    else:
        return psycopg2.connect(
            host="localhost",
            database="insurance_db",
            user="postgres",
            password="pass12345"
        )