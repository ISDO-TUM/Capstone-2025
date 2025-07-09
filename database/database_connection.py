import psycopg2
import os


def connect_to_db():  # outside_chroma=False)
    """
    Establishes a connection to the PostgreSQL database.
    Reads connection parameters from environment variables.
    """
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_name = os.getenv("DB_NAME", "papers")
    db_user = os.getenv("DB_USER", "user")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT", "5432")

    try:
        return psycopg2.connect(host=db_host, dbname=db_name,
                                user=db_user, password=db_password, port=db_port)
        # return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        # return None
        raise
