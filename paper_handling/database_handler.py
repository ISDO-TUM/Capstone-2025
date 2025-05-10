import psycopg2
from pyalex import Works
from work_parse_utils import *
from paper_metadata_retriever import *

def connect_to_db():
    return psycopg2.connect(host='localhost', dbname = 'postgres', user='postgres', password='admin',port=5432)

def insert_paper_metadata(works):
    conn = connect_to_db()
    cur = conn.cursor()

    for work in works:
        openalex_id = strip_openalex_id(work["id"])
        title = work['title']
        authors = get_authors_and_ids(work)
        year = work['publication_year']
        pdf_link = work.get('open_access', {}).get('oa_url')
        abstract = work['abstract']

        cur.execute("""
            INSERT INTO "Paper-Metadata" (OpenAlexID, Title, Authors, Year, PDFLink, Abstract)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (openalex_id, title, authors, year, pdf_link, abstract))

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

#list_tables_and_columns()

works = get_works("generative models")
insert_paper_metadata(works)