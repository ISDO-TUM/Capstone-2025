import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def connect_to_db():
    """
    Establishes a connection to the PostgreSQL database.
    Reads connection parameters from environment variables.
    """
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME", "papers")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT", "5432")

    try:
        conn = psycopg2.connect(host=db_host, dbname=db_name,
                                user=db_user, password=db_password, port=db_port)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        return None


def insert_paper(paper_data):
    """
    Inserts a new paper into the papers_table.
    'paper_data' should be a dictionary with keys: 'id', 'title', 'ref_link', 'description'.
    Note: If 'id' is auto-incrementing (SERIAL/BIGSERIAL), you might not need to pass it,
    or the table schema should handle it. For this example, we assume 'id' is provided.
    """
    if not paper_data:
        print("Error: Missing paper data.")
        return False

    conn = connect_to_db()
    if not conn:
        return False

    cur = conn.cursor()
    sql = """
          INSERT INTO papers_table (id, title, ref_link, description)
          VALUES (%s, %s, %s, %s)
          ON CONFLICT (id) DO NOTHING;
          """
    try:
        cur.execute(sql, (paper_data["id"],
                          paper_data["title"],
                          paper_data["ref_link"],
                          paper_data["description"]
                          )
                    )
        conn.commit()
        print(f"Paper with ID {paper_data['id']} inserted successfully or already existed.")
        return True
    except psycopg2.Error as e:
        print(f"Error inserting paper: {e}")
        conn.rollback()  # Rollback in case of error
        return False
    finally:
        cur.close()
        conn.close()


def get_all_papers():
    """
    Retrieves all papers from the papers_table.
    Returns a list of tuples, where each tuple represents a row.
    """
    conn = connect_to_db()
    if not conn:
        return []

    cur = conn.cursor()
    sql = "SELECT id, title, ref_link, description FROM papers_table;"
    try:
        cur.execute(sql)
        papers = cur.fetchall()
        return papers
    except psycopg2.Error as e:
        print(f"Error fetching all papers: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_paper_by_id(paper_id):
    """
    Retrieves a specific paper from the papers_table by its ID.
    Returns a tuple representing the row, or None if not found.
    """
    conn = connect_to_db()
    if not conn:
        return None

    cur = conn.cursor()
    sql = "SELECT id, title, ref_link, description FROM papers_table WHERE id = %s;"
    try:
        cur.execute(sql, (paper_id,))
        paper = cur.fetchone()
        return paper
    except psycopg2.Error as e:
        print(f"Error fetching paper by ID {paper_id}: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def update_paper_description(paper_id, new_description):
    """
    Updates the description of a paper in the papers_table.
    Returns True if update was successful, False otherwise.
    """
    conn = connect_to_db()
    if not conn:
        return False

    cur = conn.cursor()
    sql = "UPDATE papers_table SET description = %s WHERE id = %s;"
    try:
        cur.execute(sql, (new_description, paper_id))
        conn.commit()
        if cur.rowcount == 0:
            print(f"No paper found with ID {paper_id} to update.")
            return False
        print(f"Description for paper ID {paper_id} updated successfully.")
        return True
    except psycopg2.Error as e:
        print(f"Error updating paper description for ID {paper_id}: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def update_paper_title(paper_id, new_title):
    """
    Updates the title of a paper in the papers_table.
    Returns True if update was successful, False otherwise.
    """
    conn = connect_to_db()
    if not conn:
        return False

    cur = conn.cursor()
    sql = "UPDATE papers_table SET title = %s WHERE id = %s;"
    try:
        cur.execute(sql, (new_title, paper_id))
        conn.commit()
        if cur.rowcount == 0:
            print(f"No paper found with ID {paper_id} to update.")
            return False
        print(f"Title for paper ID {paper_id} updated successfully.")
        return True
    except psycopg2.Error as e:
        print(f"Error updating paper title for ID {paper_id}: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def delete_paper(paper_id):
    """
    Deletes a paper from the papers_table by its ID.
    Returns True if deletion was successful, False otherwise.
    """
    conn = connect_to_db()
    if not conn:
        return False

    cur = conn.cursor()
    sql = "DELETE FROM papers_table WHERE id = %s;"
    try:
        cur.execute(sql, (paper_id,))
        conn.commit()
        if cur.rowcount == 0:
            print(f"No paper found with ID {paper_id} to delete.")
            return False
        print(f"Paper with ID {paper_id} deleted successfully.")
        return True
    except psycopg2.Error as e:
        print(f"Error deleting paper with ID {paper_id}: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def list_tables_and_columns():
    """
    Lists all tables in the 'public' schema and their columns.
    This function remains useful for general database inspection.
    """
    conn = connect_to_db()
    if not conn:
        return

    cur = conn.cursor()

    try:
        cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    """)
        tables = cur.fetchall()
        print("Tables in 'public' schema:")
        for table in tables:
            table_name = table[0]
            print(f"- {table_name}")

            cur.execute("""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_name = %s AND table_schema = 'public'
                        """, (table_name,))
            columns = cur.fetchall()
            for column in columns:
                print(f"    - {column[0]} ({column[1]})")
    except psycopg2.Error as e:
        print(f"Error listing tables and columns: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    # 1. Make sure your .env file is set up with DB credentials
    # 2. Make sure 'papers_table' exists with columns:
    #   a: id (INT/SERIAL),
    #   b: title (TEXT),
    #   c: ref_link (TEXT),
    #   d: description (TEXT)

    print("Listing existing tables and columns:")
    list_tables_and_columns()
    print("-" * 30)
