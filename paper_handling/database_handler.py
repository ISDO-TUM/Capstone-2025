import psycopg2
import psycopg2.extras
from psycopg2 import sql as psycopg2_sql
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
    'paper_data' should be a dictionary with keys:
    'id' (string, required), 'title' (string, required),
    'abstract' (string, optional), 'authors' (string, optional),
    'publication_date' (string 'YYYY-MM-DD', optional),
    'landing_page_url' (string, optional), 'pdf_url' (string, optional).
    Uses ON CONFLICT (id) DO NOTHING to avoid duplicates if ID already exists.
    """
    if not paper_data or "id" not in paper_data or "title" not in paper_data:
        print("Error: Missing required paper data (id, title).")
        return False

    conn = connect_to_db()
    if not conn:
        return False

    cur = conn.cursor()
    sql = """
        INSERT INTO papers_table (id, title, abstract, authors, publication_date, landing_page_url, pdf_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """
    try:
        abstract = paper_data.get("abstract")
        authors = paper_data.get("authors")
        publication_date_str = paper_data.get("publication_date")
        publication_date = publication_date_str if publication_date_str and publication_date_str.strip() else None
        landing_page_url = paper_data.get("landing_page_url")
        pdf_url = paper_data.get("pdf_url")

        cur.execute(sql, (paper_data["id"],
                          paper_data["title"],
                          abstract,
                          authors,
                          publication_date,
                          landing_page_url,
                          pdf_url
                          ))
        conn.commit()
        if cur.rowcount > 0:
            print(f"Paper with ID {paper_data['id']} inserted successfully.")
        else:
            print(f"Paper with ID {paper_data['id']} already existed or insert failed silently.")
        return True
    except psycopg2.Error as e:
        print(f"Error inserting paper with ID {paper_data.get('id', 'N/A')}: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def get_all_papers():
    """
    Retrieves all papers from the papers_table.
    Returns a list of dictionaries, where each dictionary represents a paper.
    """
    conn = connect_to_db()
    if not conn:
        return []

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = "SELECT id, title, abstract, authors, publication_date, landing_page_url, pdf_url FROM papers_table;"
    try:
        cur.execute(sql)
        papers = [dict(row) for row in cur.fetchall()]
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
    Returns a dictionary representing the paper, or None if not found.
    """
    conn = connect_to_db()
    if not conn:
        return None

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = "SELECT id, title, abstract, authors, publication_date, landing_page_url, pdf_url FROM papers_table WHERE id = %s;"
    try:
        cur.execute(sql, (paper_id,))
        paper = cur.fetchone()
        return dict(paper) if paper else None
    except psycopg2.Error as e:
        print(f"Error fetching paper by ID {paper_id}: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def update_paper_field(paper_id, field_name, new_value):
    """
    Updates a specific field of a paper in the papers_table.
    Returns True if update was successful, False otherwise.
    """
    allowed_fields = ["title", "abstract", "authors", "publication_date", "landing_page_url",
                      "pdf_url"]
    if field_name not in allowed_fields:
        print(f"Error: '{field_name}' is not an updatable field for a paper.")
        return False

    conn = connect_to_db()
    if not conn:
        return False

    cur = conn.cursor()
    sql_query = psycopg2_sql.SQL("UPDATE papers_table SET {} = %s WHERE id = %s;").format(
        psycopg2_sql.Identifier(field_name)
    )
    try:
        if field_name == "publication_date" and (new_value == "" or new_value is None):
            new_value = None

        cur.execute(sql_query, (new_value, paper_id))
        conn.commit()
        if cur.rowcount == 0:
            print(
                f"No paper found with ID {paper_id} to update, or {field_name} was already set to the new value.")
            return False
        print(f"{field_name.capitalize()} for paper ID {paper_id} updated successfully.")
        return True
    except psycopg2.Error as e:
        print(f"Error updating {field_name} for paper ID {paper_id}: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def update_paper(paper_id, update_data):
    """
    Updates one or more fields of a paper in the papers_table.
    'update_data' should be a dictionary where keys are column names and values are new values.
    Example: {'title': 'New Paper Title', 'abstract': 'Updated Paper Abstract'}
    Returns True if update was successful (at least one row affected), False otherwise.
    """
    if not update_data:
        print("No data provided for paper update.")
        return False

    conn = connect_to_db()
    if not conn:
        return False

    cur = conn.cursor()

    allowed_fields = ["title", "abstract", "authors", "publication_date", "landing_page_url",
                      "pdf_url"]

    sql_set_clauses = []
    query_values = []

    for key, value in update_data.items():
        if key in allowed_fields:
            sql_set_clauses.append(psycopg2_sql.SQL("{} = %s").format(psycopg2_sql.Identifier(key)))
            if key == "publication_date" and (value == "" or value is None):
                query_values.append(None)
            else:
                query_values.append(value)
        else:
            print(
                f"Warning: Field '{key}' is not an allowed paper field for update and will be ignored.")

    if not sql_set_clauses:
        print("No valid paper fields provided for update.")
        # No actual DB operation needed, so close and return.
        cur.close()
        conn.close()
        return False

    final_set_clause = psycopg2_sql.SQL(", ").join(sql_set_clauses)

    # Construct the full query
    sql_query = psycopg2_sql.SQL("UPDATE papers_table SET {} WHERE id = %s;").format(
        final_set_clause)

    query_values.append(paper_id)

    try:
        cur.execute(sql_query, tuple(query_values))
        conn.commit()
        if cur.rowcount == 0:
            print(
                f"No paper found with ID {paper_id} to update, or fields were already set to the new values.")
            return False
        print(f"Paper with ID {paper_id} updated successfully.")
        return True
    except psycopg2.Error as e:
        print(f"Error updating paper with ID {paper_id}: {e}")
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
            ORDER BY table_name;
            """)
        tables = cur.fetchall()
        print("Tables in 'public' schema:")
        for table in tables:
            table_name = table[0]
            print(f"\n- Table: {table_name}")

            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position;
                """, (table_name,))
            columns = cur.fetchall()
            for column in columns:
                print(f"  - {column[0]} ({column[1]}, Nullable: {column[2]}, Default: {column[3]})")
    except psycopg2.Error as e:
        print(f"Error listing tables and columns: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    # 1. Make sure your .env file is set up with DB credentials.
    # 2. Ensure the 'papers_table' exists with the correct schema:
    #    CREATE TABLE papers_table (
    #        id TEXT PRIMARY KEY,
    #        title TEXT NOT NULL,
    #        abstract TEXT,
    #        authors TEXT,
    #        publication_date TEXT,
    #        landing_page_url TEXT,
    #        pdf_url TEXT
    #    );

    print("Listing existing tables and columns (initial check):")
    list_tables_and_columns()
    print("-" * 40)

    sample_paper_1 = {
        "id": "arxiv_2401.00001_paper",
        "title": "A Study on Advanced AI Models (Paper Version)",
        "abstract": "This paper explores the capabilities of advanced AI models...",
        "authors": "Jane Doe, John Smith",
        "publication_date": "2024-01-15",
        "landing_page_url": "https://example.com/paper/arxiv_2401.00001",
        "pdf_url": "https://example.com/pdf/paper/arxiv_2401.00001.pdf"
    }
    sample_paper_2 = {
        "id": "doi_10.1000_xyz123_paper",
        "title": "Quantum Entanglement in Nanostructures (Paper Version)",
        "authors": "Alice Wonderland, Bob The Builder",
        "publication_date": "2023-11-01",
        "pdf_url": "https://example.com/pdf/paper/doi_10.1000_xyz123.pdf"
    }
    sample_paper_3 = {
        "id": "internal_report_007_paper",
        "title": "Internal Research Findings (Paper)",
        "abstract": "Confidential findings for this paper.",
        "authors": "Agent K",
        "publication_date": "",
        "landing_page_url": "internal_paper_link",
    }

    insert_paper(sample_paper_1)
    insert_paper(sample_paper_2)
    insert_paper(sample_paper_3)
    print("-" * 40)

    print("\nFetching all papers:")
    all_papers = get_all_papers()
    if all_papers:
        for paper in all_papers:
            print(
                f"  ID: {paper['id']}, Title: {paper['title']}, Date: {paper['publication_date']}")
    else:
        print("  No papers found or error fetching.")
    print("-" * 40)

    print(f"\nFetching paper with ID '{sample_paper_1['id']}':")
    paper = get_paper_by_id(sample_paper_1['id'])
    if paper:
        print(f"  Found: {paper}")
    else:
        print(f"  Paper with ID {sample_paper_1['id']} not found.")
    print("-" * 40)

    print(f"\nUpdating abstract for paper ID '{sample_paper_1['id']}':")
    update_paper_field(sample_paper_1['id'], "abstract",
                       "This is an updated abstract for the AI paper.")
    paper_after_update = get_paper_by_id(sample_paper_1['id'])
    if paper_after_update:
        print(f"  Updated Abstract: {paper_after_update.get('abstract')}")
    print("-" * 40)

    print(f"\nUpdating multiple fields for paper ID '{sample_paper_2['id']}':")
    update_paper(sample_paper_2['id'], {
        "title": "Revised: Quantum Entanglement Paper",
        "authors": "Alice Wonderland, Bob The Builder, Eve The Reviewer",
        "landing_page_url": "https://newexample.com/revised_paper_doi"
    })
    paper_after_multi_update = get_paper_by_id(sample_paper_2['id'])
    if paper_after_multi_update:
        print(f"  Updated Paper: {paper_after_multi_update}")
    print("-" * 40)

    print(f"\nDeleting paper with ID '{sample_paper_3['id']}':")
    delete_paper(sample_paper_3['id'])
    paper_after_delete = get_paper_by_id(sample_paper_3['id'])
    if not paper_after_delete:
        print(f"  Paper with ID {sample_paper_3['id']} successfully deleted or was not found.")
    print("-" * 40)

    print("\nFinal listing of tables and columns:")
    list_tables_and_columns()
    print("-" * 40)

    print("\nTesting non-existent paper operations:")
    get_paper_by_id("non_existent_paper_id")
    update_paper_field("non_existent_paper_id", "title", "New Title")
    update_paper("non_existent_paper_id", {"title": "New Title"})
    delete_paper("non_existent_paper_id")
