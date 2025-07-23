"""
This module handles all paper-related database operations for the Capstone project.

Responsibilities:
- Inserting, updating, and deleting paper records in the database
- Generating and managing paper hashes for deduplication
- Fetching papers by hash, ID, or project linkage
- Utility functions for paper metadata normalization and status codes

All database operations are designed to be robust, transactional, and reusable by the agent and API layers.
"""

import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
import hashlib
from utils.status import Status
import json
from database.database_connection import connect_to_db

load_dotenv()


def _generate_paper_hash(paper_data_dict):
    """
    Generate a SHA256 hash from specific fields of a paper data dictionary for deduplication.
    Args:
        paper_data_dict (dict): Dictionary containing paper metadata fields.
    Returns:
        str: SHA256 hash string representing the paper's unique identity.
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


def insert_papers(papers_data_list):
    """
    Insert one or more paper records into the papers_table, including extra metrics.
    Args:
        papers_data_list (list[dict]): List of paper metadata dicts to insert.
    Returns:
        tuple: (status_code, inserted_details)
            - status_code: Status.SUCCESS if at least one row inserted, Status.FAILURE otherwise.
            - inserted_details: List of dicts with 'title', 'abstract', and 'hash' for each inserted paper.
    Side effects:
        Inserts new rows into the database and commits the transaction.
    """
    # ---------------- upfront checks -----------------
    if not isinstance(papers_data_list, list):
        print("insert_papers expects a list of dicts.")
        return Status.FAILURE, []

    if not papers_data_list:
        return Status.SUCCESS, []

    # ---------------- DB connection ------------------
    conn = connect_to_db()
    if conn is None:
        return Status.FAILURE, []

    cur = conn.cursor(cursor_factory=extras.DictCursor)

    SQL = """
        INSERT INTO public.papers_table (
            paper_hash, id, title, abstract, authors,
            publication_date, landing_page_url, pdf_url,
            similarity_score, fwci, citation_normalized_percentile,
            cited_by_count, counts_by_year
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (paper_hash) DO NOTHING;
    """

    inserted_details = []

    # ---------------- main loop ----------------------
    for p in papers_data_list:
        if not isinstance(p, dict) or "id" not in p or "title" not in p:
            print(f"Skipping malformed record: {p!r}")
            continue

        try:
            p_hash = _generate_paper_hash(p)

            abstract = p.get("abstract")
            authors = p.get("authors")
            pub_date = p.get("publication_date")
            landing_url = p.get("landing_page_url")
            pdf_url = p.get("pdf_url")

            sim_score = _to_float(p.get("similarity_score"))
            fwci = _to_float(p.get("fwci"))

            # ---------- NEW: pull only the numeric percentile ----------
            cit_norm_raw = p.get("citation_normalized_percentile")
            cit_norm_pct = _to_float(cit_norm_raw["value"]) if isinstance(cit_norm_raw, dict) else None

            cited_count = _to_int(p.get("cited_by_count"))

            counts_years = p.get("counts_by_year")
            if counts_years is not None:
                counts_years = json.dumps(counts_years)          # -> JSONB text

            cur.execute(
                SQL,
                (
                    p_hash, p["id"], p["title"], abstract, authors,
                    pub_date, landing_url, pdf_url,
                    sim_score, fwci, cit_norm_pct,
                    cited_count, counts_years
                ),
            )

            if cur.rowcount:
                inserted_details.append(
                    {"title": p["title"], "abstract": abstract or "", "hash": p_hash}
                )

        except psycopg2.Error as db_err:
            print(f"[DB] error inserting {p.get('id')}: {db_err.diag.message_primary}")
            conn.rollback()

    # --------------- finalise ------------------------
    conn.commit()
    cur.close()
    conn.close()

    status_code = Status.SUCCESS if inserted_details else Status.FAILURE
    return status_code, inserted_details


def get_all_papers():
    """
    Retrieve all papers from the papers_table.
    Returns:
        list[dict]: List of all paper records as dictionaries.
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
    Retrieve all versions of a paper from the papers_table by its original ID.
    Args:
        original_id (str): The original paper ID.
    Returns:
        list[dict]: List of paper versions as dictionaries.
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
    Retrieve a specific paper version from the papers_table by its unique hash.
    Args:
        paper_hash_to_find (str): The paper hash to look up.
    Returns:
        dict or None: Paper record as a dictionary, or None if not found.
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
    Retrieve one or more papers from papers_table by their unique hashes, preserving input order.
    Args:
        paper_hashes_to_find (list[str]): List of paper_hash strings.
    Returns:
        list[dict]: List of paper records as dictionaries, in the same order as input hashes.
    """
    if not isinstance(paper_hashes_to_find, list) or not paper_hashes_to_find:
        print("Error: Input must be a non-empty list of paper hashes.")
        return []

    conn = connect_to_db()
    if not conn:
        return []

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = """
        SELECT
            paper_hash,
            id,
            title,
            abstract,
            authors,
            publication_date,
            landing_page_url,
            pdf_url,
            similarity_score,
            fwci,
            citation_normalized_percentile,
            cited_by_count,
            counts_by_year
        FROM papers_table
        WHERE paper_hash = ANY(%s);
    """

    try:
        cur.execute(sql, (paper_hashes_to_find,))
        papers_dict = {row['paper_hash']: dict(row) for row in cur.fetchall()}

        # Preserve the order of the input hashes
        papers = []
        for hash_value in paper_hashes_to_find:
            if hash_value in papers_dict:
                papers.append(papers_dict[hash_value])

        return papers
    except psycopg2.Error as e:
        print(f"Error fetching papers by hashes {paper_hashes_to_find}: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def update_paper(old_paper_hash, update_data):
    """
    Update one or more fields of a specific paper version.
    Args:
        old_paper_hash (str): The hash of the paper to update.
        update_data (dict): Dictionary of fields to update.
    Returns:
        bool: True if update was successful, False otherwise.
    Side effects:
        Inserts a new version of the paper and deletes the old version in the database.
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
    Update a specific field of a paper version identified by 'old_paper_hash'.
    Args:
        old_paper_hash (str): The hash of the paper to update.
        field_name (str): The field to update.
        new_value: The new value for the field.
    Returns:
        bool: True if update was successful, False otherwise.
    """

    allowed_fields = ["id", "title", "abstract", "authors", "publication_date", "landing_page_url",
                      "pdf_url"]
    if field_name not in allowed_fields:
        print(f"Error: '{field_name}' is not an updatable field for a paper.")
        return False
    return update_paper(old_paper_hash, {field_name: new_value})


def delete_paper_by_hash(paper_hash_to_delete):
    """
    Delete a specific paper version from the papers_table by its unique hash.
    Args:
        paper_hash_to_delete (str): The hash of the paper to delete.
    Returns:
        bool: True if deletion was successful, False otherwise.
    Side effects:
        Removes the paper from the database.
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
    List all tables in the 'public' schema and their columns, focusing on 'papers_table'.
    Returns:
        None. Prints schema information to stdout.
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


# HELPER functions
def _to_float(val):
    """
    Convert a value to float if possible, else return None.
    Args:
        val: Value to convert.
    Returns:
        float or None
    """
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _to_int(val):
    """
    Convert a value to int if possible, else return None.
    Args:
        val: Value to convert.
    Returns:
        int or None
    """
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


if __name__ == '__main__':

    # 1. Make sure your .env file is set up with DB credentials.
    # 2. Ensure the 'papers_table' exists with the correct schema.
    #    You might need to DROP and RECREATE it if the schema changed significantly.
    #
    #    Example CREATE TABLE statement:
    #    DROP TABLE IF EXISTS papers_table; -- If you want to start fresh for testing
    #    CREATE TABLE papers_table (
    #        paper_hash TEXT PRIMARY KEY,     -- Hash of content fields
    #        id TEXT NOT NULL,                -- Original external ID
    #        title TEXT NOT NULL,
    #        abstract TEXT,
    #        authors TEXT,
    #        publication_date TEXT,
    #        landing_page_url TEXT,
    #        pdf_url TEXT
    #    );

    print("Listing existing table schema (initial check):")
    list_tables_and_columns()
    print("-" * 40)

    sample_paper_1_data = {
        "id": "arxiv_2401.00001_v1",
        "title": "A Study on Advanced AI Models",
        "abstract": "This paper explores advanced AI models.",
        "authors": "Jane Doe, John Smith",
        "publication_date": "2024-01-15",
        "landing_page_url": "https://example.com/paper/arxiv_2401.00001",
        "pdf_url": "https://example.com/pdf/paper/arxiv_2401.00001.pdf"
    }
    sample_paper_2_data = {
        "id": "doi_10.1000_xyz123",
        "title": "Quantum Entanglement in Nanostructures",
        "authors": "Alice Wonderland, Bob The Builder",
        "publication_date": "2023-11-01",
        "abstract": None,
        "pdf_url": "https://example.com/pdf/paper/doi_10.1000_xyz123.pdf"
    }
    sample_paper_3_data = {
        "id": "internal_report_007",
        "title": "Internal Research Findings",
        "abstract": "Confidential findings.",
        "authors": "Agent K",
        "publication_date": "",
        "landing_page_url": "internal_paper_link",
    }

    paper_1_hash = None
    paper_2_hash = None
    paper_3_hash = None

    print("\nAttempting to insert papers:")
    papers_to_insert = [sample_paper_1_data, sample_paper_2_data, sample_paper_3_data,
                        sample_paper_1_data]
    status_code, inserted_info = insert_papers(papers_to_insert)

    print(f"Insertion Status Code: {status_code}")
    if status_code == 1:
        print("Successfully inserted papers:")
        for info in inserted_info:
            print(f"  Title: {info['title']}, Abstract: '{info['abstract']}', Hash: {info['hash']}")

            if info['title'] == sample_paper_1_data['title']:
                paper_1_hash = info['hash']
            elif info['title'] == sample_paper_2_data['title']:
                paper_2_hash = info['hash']
            elif info['title'] == sample_paper_3_data['title']:
                paper_3_hash = info['hash']
    elif not inserted_info:
        print("  No new papers were inserted (possibly all duplicates or all data invalid).")
    else:
        print("  Insertion was reported as unsuccessful.")
        if inserted_info:
            print(f"  Partial/erroneous info (should be empty on error): {inserted_info}")

    # print("-" * 40)
    #
    # print("\nFetching all papers:")
    # all_papers = get_all_papers()
    # if all_papers:
    #     for paper in all_papers:
    #         print(f"  Hash: {paper['paper_hash']}, OrigID: {paper['id']}, Title: {paper['title']}")
    # else:
    #     print("  No papers found or error fetching.")
    # print("-" * 40)
    #
    # if paper_1_hash:
    #     print(f"\nFetching paper by its hash '{paper_1_hash}':")
    #     paper = get_paper_by_hash(paper_1_hash)
    #     if paper:
    #         print(f"  Found: {paper}")
    #     else:
    #         print(f"  Paper with hash {paper_1_hash} not found (should exist).")
    #
    #     print(f"\nFetching paper versions by original ID '{sample_paper_1_data['id']}':")
    #     paper_versions = get_papers_by_original_id(sample_paper_1_data['id'])
    #     if paper_versions:
    #         print(f"  Found {len(paper_versions)} version(s):")
    #         for p_v in paper_versions:
    #             print(f"    Hash: {p_v['paper_hash']}, Title: {p_v['title']}")
    #     else:
    #         print(f"  Paper with original ID {sample_paper_1_data['id']} not found.")
    #     print("-" * 40)
    #
    #     print(f"\nUpdating abstract for paper hash '{paper_1_hash}':")
    #     updated_abstract = "This is an updated abstract for the AI paper, version 2."
    #     if update_paper_field(paper_1_hash, "abstract", updated_abstract):
    #
    #         temp_updated_data = sample_paper_1_data.copy()
    #         temp_updated_data["abstract"] = updated_abstract
    #         new_paper_1_hash = _generate_paper_hash(temp_updated_data)
    #
    #         print(
    #             f"  Update reported success. Old hash was {paper_1_hash}, new hash should be {new_paper_1_hash}.")
    #         paper_after_update = get_paper_by_hash(new_paper_1_hash)
    #         if paper_after_update:
    #             print(f"  Retrieved updated paper. Abstract: {paper_after_update.get('abstract')}")
    #             paper_1_hash = new_paper_1_hash
    #         else:
    #             print(
    #                 f"  Could not retrieve paper by new hash {new_paper_1_hash}. Update might have failed silently or hash mismatch.")
    #     else:
    #         print("  Update failed.")
    #     print("-" * 40)
    #
    # if paper_2_hash:
    #     print(f"\nUpdating multiple fields for paper hash '{paper_2_hash}':")
    #     update_payload = {
    #         "title": "Revised: Quantum Entanglement Paper (v2)",
    #         "authors": "Alice Wonderland, Bob The Builder, Eve The Reviewer",
    #         "landing_page_url": "https://newexample.com/revised_paper_doi"
    #     }
    #     if update_paper(paper_2_hash, update_payload):
    #         temp_updated_data_p2 = sample_paper_2_data.copy()
    #         temp_updated_data_p2.update(update_payload)
    #         new_paper_2_hash = _generate_paper_hash(temp_updated_data_p2)
    #
    #         print(
    #             f"  Multi-field update reported success. Old hash {paper_2_hash}, new hash {new_paper_2_hash}.")
    #         paper_after_multi_update = get_paper_by_hash(new_paper_2_hash)
    #         if paper_after_multi_update:
    #             print(f"  Updated Paper (retrieved by new hash): {paper_after_multi_update}")
    #             paper_2_hash = new_paper_2_hash
    #         else:
    #             print(f"  Could not retrieve paper by new hash {new_paper_2_hash}.")
    #
    #     else:
    #         print("  Multi-field update failed.")
    #     print("-" * 40)
    #
    # if paper_3_hash:
    #     print(f"\nDeleting paper with hash '{paper_3_hash}':")
    #     if delete_paper_by_hash(paper_3_hash):
    #         paper_after_delete = get_paper_by_hash(paper_3_hash)
    #         if not paper_after_delete:
    #             print(f"  Paper with hash {paper_3_hash} successfully deleted.")
    #         else:
    #             print(
    #                 f"  Paper with hash {paper_3_hash} still found after reported deletion. This is an error.")
    #     else:
    #         print(f"  Deletion of paper with hash {paper_3_hash} failed.")
    # else:
    #     print(
    #         "\nSkipping delete test for paper 3 as its hash was not captured (insertion might have failed).")
    # print("-" * 40)
    #
    # print("\nFinal listing of table schema:")
    # list_tables_and_columns()
    # print("-" * 40)
    #
    # print("\nTesting non-existent paper operations:")
    # non_existent_hash = "non_existent_paper_hash_value_12345"
    # print(f"Attempting to get paper by non-existent hash: {non_existent_hash}")
    # get_paper_by_hash(non_existent_hash)
    # print(f"Attempting to update paper by non-existent hash: {non_existent_hash}")
    # update_paper_field(non_existent_hash, "title", "New Title")
    # print(f"Attempting to delete paper by non-existent hash: {non_existent_hash}")
    # delete_paper_by_hash(non_existent_hash)
    #
    # print("\nTesting batch retrieval using get_papers_by_hash():")
    # if paper_1_hash and paper_2_hash:
    #     print(f"  Fetching papers by existing hashes: {paper_1_hash}, {paper_2_hash}")
    #     found_papers = get_papers_by_hash([paper_1_hash, paper_2_hash])
    #     if found_papers:
    #         print(f"  Found {len(found_papers)} paper(s):")
    #         for paper in found_papers:
    #             print(f"    - Hash: {paper['paper_hash']}, Title: {paper['title']}")
    #     else:
    #         print("  No papers were found (unexpected).")
    # else:
    #     print("  Skipping existing hash test due to missing hash values.")
    #
    # print("\n  Fetching papers by non-existent hashes:")
    # fake_hashes = ["not_a_real_hash_1", "not_a_real_hash_2"]
    # missing_papers = get_papers_by_hash(fake_hashes)
    # if not missing_papers:
    #     print("  Correctly found no matching papers.")
    # else:
    #     print(f"  Unexpectedly found {len(missing_papers)} paper(s):")
    #     for paper in missing_papers:
    #         print(f"    - Hash: {paper['paper_hash']}, Title: {paper['title']}")
    #
    # print("-" * 40)
    print("Test script finished.")
