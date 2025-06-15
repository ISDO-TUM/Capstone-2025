import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
import hashlib
from utils.status import Status
from typing import List, Dict

load_dotenv()


def _generate_paper_hash(paper_data_dict):
    """
    Generates a SHA256 hash from specific fields of a paper data dictionary.
    Ensures consistent ordering and handling of None values for hashing.
    All relevant fields: id, title, abstract, authors, publication_date, landing_page_url, pdf_url
    """

    def s(value):
        if value is None:
            return ""
        return str(value)

    fields_to_hash = [
        s(paper_data_dict.get("id")),
        s(paper_data_dict.get("title")),
        s(paper_data_dict.get("abstract")),
        s(paper_data_dict.get("authors")),
        s(paper_data_dict.get("publication_date")),
        s(paper_data_dict.get("landing_page_url")),
        s(paper_data_dict.get("pdf_url"))
    ]

    data_string = "||".join(fields_to_hash)
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()


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


def insert_papers(papers_data_list):
    """
    Inserts one or more new papers into the papers_table.
    'papers_data_list' should be a list of dictionaries. Each dictionary requires:
    'id' (string, original identifier), 'title' (string). Optional fields:
    'abstract', 'authors', 'publication_date' ('YYYY-MM-DD'), 'landing_page_url', 'pdf_url'.

    A hash is generated from all paper fields and used as the primary key.
    If a paper with the exact same content (and thus same hash) already exists,
    it's skipped due to ON CONFLICT (paper_hash) DO NOTHING.

    Returns a tuple: (status_code, list_of_inserted_paper_info).
    status_code: 1 if at least one paper was successfully inserted, 0 otherwise (or on error).
    list_of_inserted_paper_info: List of dicts [{"title": str, "abstract": str, "hash": str}]
                                 for each newly inserted paper.
    """
    if not isinstance(papers_data_list, list):
        print("Error: Input must be a list of paper dictionaries.")
        return (Status.SUCCESS, [])
    if not papers_data_list:
        print("No papers provided for insertion.")
        return (Status.SUCCESS, [])

    conn = connect_to_db()
    if not conn:
        return Status.SUCCESS, []

    inserted_papers_details = []
    cur = conn.cursor()
    sql_insert = """
        INSERT INTO papers_table (paper_hash, id, title, abstract, authors, publication_date, landing_page_url, pdf_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (paper_hash) DO NOTHING;
    """

    for paper_data in papers_data_list:
        if not paper_data or not isinstance(paper_data, dict) or \
                paper_data.get("id") is None or paper_data.get("title") is None:
            print(
                f"Error: Missing required fields (id, title) or invalid data for a paper. Skipping: {str(paper_data)[:100]}")
            continue

        try:
            current_hash = _generate_paper_hash(paper_data)

            abstract = paper_data.get("abstract")
            authors = paper_data.get("authors")
            publication_date_str = paper_data.get("publication_date")
            publication_date = publication_date_str if publication_date_str and str(
                publication_date_str).strip() else None
            landing_page_url = paper_data.get("landing_page_url")
            pdf_url = paper_data.get("pdf_url")

            cur.execute(sql_insert, (
                current_hash,
                paper_data["id"],
                paper_data["title"],
                abstract,
                authors,
                publication_date,
                landing_page_url,
                pdf_url
            ))

            if cur.rowcount > 0:
                inserted_papers_details.append({
                    "title": paper_data["title"],
                    "abstract": str(abstract) if abstract is not None else "",
                    "hash": current_hash
                })
        except psycopg2.Error as e:
            print(
                f"Database error inserting paper with original ID {paper_data.get('id', 'N/A')}: {e}")
            conn.rollback()
            cur.close()
            conn.close()
            return (Status.SUCCESS, [])
        except Exception as ex:
            print(
                f"An unexpected error occurred processing paper ID {paper_data.get('id', 'N/A')}: {ex}")
            conn.rollback()
            cur.close()
            conn.close()
            return (Status.SUCCESS, [])

    if not inserted_papers_details:
        conn.commit()
        status_code = Status.SUCCESS
    else:
        conn.commit()
        status_code = Status.FAILURE

    cur.close()
    conn.close()
    return (status_code, inserted_papers_details)


def get_all_papers():
    """
    Retrieves all papers (all versions) from the papers_table.
    Returns a list of dictionaries, where each dictionary represents a paper version.
    """
    conn = connect_to_db()
    if not conn:
        return []

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = "SELECT paper_hash, id, title, abstract, authors, publication_date, landing_page_url, pdf_url FROM papers_table;"
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

def get_papers_after_date(date_after: str) -> List[Dict[str, object]]:
    """
    Retrieves every paper version whose ``publication_date`` is **strictly later**
    than *date_after*.

    Parameters
    ----------
    date_after : str
        ISO-formatted date string ``"YYYY-MM-DD"``.
        Example: ``"2025-05-01"`` will return papers dated **after** 1 May 2025.

    Returns
    -------
    list[dict]
        Zero or more dictionaries with keys
        ``paper_hash``, ``id``, ``title``, ``abstract``, ``authors``,
        ``publication_date``, ``landing_page_url``, and ``pdf_url``.
        An empty list is returned on connection or query failure.
    """
    conn = connect_to_db()
    if not conn:
        return []

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = """
        SELECT paper_hash,
               id,
               title,
               abstract,
               authors,
               publication_date,
               landing_page_url,
               pdf_url
        FROM   papers_table
        WHERE  publication_date IS NOT NULL
          AND  publication_date > %s;
    """
    try:
        cur.execute(sql, (date_after,))
        return [dict(row) for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Error fetching papers after {date_after}: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_all_papers():
    """
    Retrieves all papers (all versions) from the papers_table.
    Returns a list of dictionaries, where each dictionary represents a paper version.
    """
    conn = connect_to_db()
    if not conn:
        return []

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = "SELECT paper_hash, id, title, abstract, authors, publication_date, landing_page_url, pdf_url FROM papers_table;"
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


def get_papers_by_original_id(original_id):
    """
    Retrieves all versions of a paper from the papers_table by its original ID.
    Returns a list of dictionaries representing paper versions, or an empty list if not found.
    """
    conn = connect_to_db()
    if not conn:
        return []

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = "SELECT paper_hash, id, title, abstract, authors, publication_date, landing_page_url, pdf_url FROM papers_table WHERE id = %s;"
    try:
        cur.execute(sql, (original_id,))
        papers = [dict(row) for row in cur.fetchall()]
        return papers
    except psycopg2.Error as e:
        print(f"Error fetching papers by original ID {original_id}: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_paper_by_hash(paper_hash_to_find):
    """
    Retrieves a specific paper version from the papers_table by its unique hash.
    Returns a dictionary representing the paper, or None if not found.
    """
    conn = connect_to_db()
    if not conn:
        return None

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = "SELECT paper_hash, id, title, abstract, authors, publication_date, landing_page_url, pdf_url FROM papers_table WHERE paper_hash = %s;"
    try:
        cur.execute(sql, (paper_hash_to_find,))
        paper = cur.fetchone()
        return dict(paper) if paper else None
    except psycopg2.Error as e:
        print(f"Error fetching paper by hash {paper_hash_to_find}: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def get_papers_by_hash(paper_hashes_to_find):
    """
    Retrieves multiple paper versions from the papers_table by their unique hashes.
    'paper_hashes_to_find' should be a list of hashes.
    Returns a list of dictionaries representing the papers, or an empty list if none found.
    """
    if not isinstance(paper_hashes_to_find, list) or not paper_hashes_to_find:
        print("Error: Input must be a non-empty list of paper hashes.")
        return []

    conn = connect_to_db()
    if not conn:
        return []

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = "SELECT paper_hash, id, title, abstract, authors, publication_date, landing_page_url, pdf_url FROM papers_table WHERE paper_hash = ANY(%s);"
    try:
        cur.execute(sql, (paper_hashes_to_find,))
        papers = [dict(row) for row in cur.fetchall()]
        return papers
    except psycopg2.Error as e:
        print(f"Error fetching papers by hashes {paper_hashes_to_find}: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def update_paper(old_paper_hash, update_data):
    """
    Updates one or more fields of a specific paper version.
    This operation involves fetching the paper by 'old_paper_hash',
    applying 'update_data', generating a 'new_paper_hash',
    inserting the new version, and deleting the old version.
    'update_data' is a dictionary of fields to change.
    Returns True if update was successful, False otherwise.
    """
    if not update_data:
        print("No data provided for paper update.")
        return False

    conn = connect_to_db()
    if not conn:
        return False

    cur = conn.cursor()

    try:

        cur.execute(
            "SELECT id, title, abstract, authors, publication_date, landing_page_url, pdf_url FROM papers_table WHERE paper_hash = %s;",
            (old_paper_hash,))
        current_paper_tuple = cur.fetchone()

        if not current_paper_tuple:
            print(f"No paper found with hash {old_paper_hash} to update.")
            return False

        current_paper_data = {
            "id": current_paper_tuple[0], "title": current_paper_tuple[1],
            "abstract": current_paper_tuple[2], "authors": current_paper_tuple[3],
            "publication_date": current_paper_tuple[4],
            "landing_page_url": current_paper_tuple[5], "pdf_url": current_paper_tuple[6]
        }

        updated_paper_data = current_paper_data.copy()

        allowed_fields = ["id", "title", "abstract", "authors", "publication_date",
                          "landing_page_url", "pdf_url"]

        valid_update_applied = False
        for key, value in update_data.items():
            if key in allowed_fields:
                if key == "publication_date" and (value == "" or value is None):
                    updated_paper_data[key] = None
                else:
                    updated_paper_data[key] = value
                valid_update_applied = True
            else:
                print(
                    f"Warning: Field '{key}' is not an allowed paper field for update and will be ignored.")

        if not valid_update_applied:
            print("No valid fields provided for update.")

            return True

        new_hash = _generate_paper_hash(updated_paper_data)

        if new_hash == old_paper_hash:
            print(
                f"Update for paper hash {old_paper_hash} resulted in no change to content hash. No DB modification needed.")
            return True

        insert_sql = """
            INSERT INTO papers_table (paper_hash, id, title, abstract, authors, publication_date, landing_page_url, pdf_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (paper_hash) DO NOTHING;
        """

        cur.execute(insert_sql, (
            new_hash,
            updated_paper_data["id"], updated_paper_data["title"],
            updated_paper_data.get("abstract"), updated_paper_data.get("authors"),
            updated_paper_data.get("publication_date"),
            updated_paper_data.get("landing_page_url"), updated_paper_data.get("pdf_url")
        ))

        rows_inserted = cur.rowcount
        if rows_inserted == 0 and new_hash != old_paper_hash:
            print(
                f"Updated state for paper (old hash {old_paper_hash}) results in new hash {new_hash}, which already exists in the DB.")

        delete_sql = "DELETE FROM papers_table WHERE paper_hash = %s;"
        cur.execute(delete_sql, (old_paper_hash,))

        if cur.rowcount == 0:
            print(
                f"Warning: Paper with old hash {old_paper_hash} was not found for deletion after update attempt. This might be okay if the new state's hash ({new_hash}) was identical and already existed.")

        conn.commit()
        print(
            f"Paper with old hash {old_paper_hash} processed for update. New effective hash is {new_hash}.")
        return True

    except psycopg2.Error as e:
        print(f"Error updating paper with old hash {old_paper_hash}: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as ex:
        print(f"An unexpected error occurred while updating paper {old_paper_hash}: {ex}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def update_paper_field(old_paper_hash, field_name, new_value):
    """
    Updates a specific field of a paper version identified by 'old_paper_hash'.
    This is a convenience function that calls 'update_paper'.
    Returns True if update was successful, False otherwise.
    """

    allowed_fields = ["id", "title", "abstract", "authors", "publication_date", "landing_page_url",
                      "pdf_url"]
    if field_name not in allowed_fields:
        print(f"Error: '{field_name}' is not an updatable field for a paper.")
        return False
    return update_paper(old_paper_hash, {field_name: new_value})


def delete_paper_by_hash(paper_hash_to_delete):
    """
    Deletes a specific paper version from the papers_table by its unique hash.
    Returns True if deletion was successful, False otherwise.
    """
    conn = connect_to_db()
    if not conn:
        return False

    cur = conn.cursor()
    sql = "DELETE FROM papers_table WHERE paper_hash = %s;"
    try:
        cur.execute(sql, (paper_hash_to_delete,))
        conn.commit()
        if cur.rowcount == 0:
            print(f"No paper found with hash {paper_hash_to_delete} to delete.")
            return False
        print(f"Paper with hash {paper_hash_to_delete} deleted successfully.")
        return True
    except psycopg2.Error as e:
        print(f"Error deleting paper with hash {paper_hash_to_delete}: {e}")
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
            WHERE table_schema = 'public' AND table_name = 'papers_table' -- Focus on papers_table
            ORDER BY table_name;
            """)
        tables = cur.fetchall()
        if not tables:
            print("Table 'papers_table' not found in 'public' schema.")
            return

        print("Schema for 'papers_table':")
        for table in tables:
            table_name = table[0]
            cur.execute("""
                SELECT c.column_name, c.data_type, c.is_nullable, c.column_default,
                       tc.constraint_name, tc.constraint_type
                FROM information_schema.columns c
                LEFT JOIN information_schema.key_column_usage kcu
                  ON c.table_schema = kcu.table_schema
                  AND c.table_name = kcu.table_name
                  AND c.column_name = kcu.column_name
                LEFT JOIN information_schema.table_constraints tc
                  ON kcu.constraint_schema = tc.constraint_schema
                  AND kcu.constraint_name = tc.constraint_name
                WHERE c.table_name = %s AND c.table_schema = 'public'
                ORDER BY c.ordinal_position;
                """, (table_name,))
            columns = cur.fetchall()
            for column in columns:
                constraint_info = ""
                if column[4] and column[5]:  # constraint_name and constraint_type
                    constraint_info = f", Constraint: {column[4]} ({column[5]})"
                print(
                    f"  - {column[0]} ({column[1]}, Nullable: {column[2]}, Default: {column[3]}{constraint_info})")
    except psycopg2.Error as e:
        print(f"Error listing tables and columns: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':

    get_all_papers()
