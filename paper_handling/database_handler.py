import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def connect_to_db():
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME", "papers")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT", "5432")

    return psycopg2.connect(host=db_host, dbname=db_name,
                            user=db_user, password=db_password, port=db_port)


def insert_works_data(works):
    conn = connect_to_db()
    cur = conn.cursor()

    for work in works:
        cur.execute("""
                    INSERT INTO "Paper-Metadata" (OpenAlexID, Title, Abstract, Authors, PublicationDate, LandingPageURL,
                                                  PdfURL)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """, (work["id"],
                          work["title"],
                          work["abstract"],
                          work["authors"],
                          work["publication_date"],
                          work["landing_page_url"],
                          work["pdf_url"]
                          )
                    )

    conn.commit()

    cur.close()
    conn.close()


def list_tables_and_columns():
    conn = connect_to_db()
    cur = conn.cursor()

    # List all tables in the current schema (usually 'public')
    cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """)

    tables = cur.fetchall()
    print("Tables:")
    for table in tables:
        print(f"- {table[0]}")

        # Get columns for each table
        cur.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = %s
                    """, (table[0],))

        columns = cur.fetchall()
        for column in columns:
            print(f"    - {column[0]} ({column[1]})")

    cur.close()
    conn.close()
