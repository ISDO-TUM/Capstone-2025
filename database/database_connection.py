import psycopg2
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT


def connect_to_db():  # outside_chroma=False)
    """
    Establishes a connection to the PostgreSQL database.
    Reads connection parameters from centralized config module.
    """
    db_host = DB_HOST
    db_name = DB_NAME
    db_user = DB_USER
    db_password = DB_PASSWORD
    db_port = DB_PORT

    try:
        return psycopg2.connect(
            host=db_host,
            dbname=db_name,
            user=db_user,
            password=db_password,
            port=db_port,
        )
        # return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        # return None
        raise
