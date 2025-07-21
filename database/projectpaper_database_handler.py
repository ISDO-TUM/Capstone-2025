"""
This module handles all project-paper linking and rating operations for the Capstone project.

Responsibilities:
- Linking papers to projects in the paperprojects_table
- Managing paper ratings, newsletter tags, and seen status
- Fetching, updating, and deleting project-paper associations

All project-paper operations are designed to be robust, transactional, and reusable by the agent and API layers.
"""

import psycopg2
import psycopg2.extras
from database.database_connection import connect_to_db
from datetime import datetime, timedelta


def assign_paper_to_project(paper_hash: str, project_id: str, summary: str, newsletter: bool = False, seen: bool = False, is_replacement: bool = False):
    """
    After papers for a project have been chosen with similarity search, the papers are linked to a project
    in paperprojects_table one by one using this function which adds entries to that table.
    Args:
        paper_hash: The paper's hash
        project_id: The project's id
        summary: An agent-generated explanation on why this paper is relevant for the project
        newsletter: If the paper belongs to pubsub
        seen: If the paper has been seen by the user in the frontend (must have newsletter = true to have this set to true)

    Returns: void

    """
    connection = connect_to_db()
    cursor = connection.cursor()

    cursor.execute("""INSERT INTO paperprojects_table (project_id, paper_hash, summary, newsletter, seen, is_replacement) VALUES (%s, %s, %s, %s, %s, %s)
                      ON CONFLICT (project_id, paper_hash)
                      DO UPDATE SET summary = EXCLUDED.summary, is_replacement = EXCLUDED.is_replacement
        """, (project_id, paper_hash, summary, newsletter, seen, is_replacement))
    connection.commit()
    cursor.close()
    connection.close()


def get_papers_for_project(project_id: str):
    """
    Returns the list of papers for a project by linking by hash the papers from paperprojects_table
    with the ones from papers_table. Excludes pubsub papers.
    Args:
        project_id: The project's id

    Returns: A dict list where each dict contains paper metadata + a summary explaining why the paper is relevant

    """
    connection = connect_to_db()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
                   SELECT papers_table.*, paperprojects_table.rating, paperprojects_table.is_replacement
                   FROM papers_table
                            JOIN paperprojects_table ON papers_table.paper_hash = paperprojects_table.paper_hash
                   WHERE paperprojects_table.project_id = %s
                     AND paperprojects_table.excluded = FALSE
                     AND paperprojects_table.newsletter = FALSE
                   """, (project_id,))
    papers = cursor.fetchall()
    results = []
    for paper in papers:
        paper_dict = {}
        cursor.execute("""
                       SELECT summary
                       FROM paperprojects_table
                       WHERE paper_hash = %s
                         AND project_id = %s
                       """, (paper['paper_hash'], project_id))

        summary_row = cursor.fetchone()
        paper_dict['paper_hash'] = dict(paper)['paper_hash']
        paper_dict['rating'] = paper['rating']
        paper_dict['is_replacement'] = paper['is_replacement']
        if summary_row:
            paper_dict['summary'] = summary_row[0]
        print(paper_dict)
        results.append(paper_dict)
    print("Successfully converted papers to dict")
    return results


def set_newsletter_tags_for_project(project_id: str, paper_hashes: list, summaries: list):
    """
    Adds papers to a project in paperprojects_table by setting newsletter to true and seen to false to a set of papers
    identified by paper_hashes.
    These papers correspond to the pubsub system.
    Each paper needs a summary explaining why the paper is relevant to the project even if the paper is already in the table.
    If a papers is already linked to the paper we just update the values of newsletter and seen and ignore the summary.
    Args:
        project_id: The project's id
        paper_hashes: List of paper hashes
        summaries: List of paper summaries
    Returns:
        void

    """
    connection = connect_to_db()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Prepare data: List of tuples (project_id, paper_hash, newsletter, seen)
    values = [(project_id, paper_hash, summary, True, False) for (paper_hash, summary) in zip(paper_hashes, summaries)]

    query = """
            INSERT INTO paperprojects_table (project_id, paper_hash, summary, newsletter, seen)
            VALUES %s ON CONFLICT (project_id, paper_hash)
            DO UPDATE SET
                newsletter = EXCLUDED.newsletter,
                seen = EXCLUDED.seen;
            """

    psycopg2.extras.execute_values(cursor, query, values)

    connection.commit()
    cursor.close()
    connection.close()


def reset_newsletter_tags(project_id: str):
    """
    Resets the newsletter and seen tags to 'False' for a project in paperprojects_table
    Args:
        project_id: The project's id

    Returns:
        void
    """
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE paperprojects_table
           SET newsletter = FALSE,
               seen       = FALSE
         WHERE project_id = %s;
    """, (project_id,))
    connection.commit()
    cursor.close()
    connection.close()


def get_pubsub_papers_for_project(project_id: str):
    """
    Returns the list of pubsub papers for a project.
    Args:
        project_id: The project's id

    Returns:
        A list of paper hashes and their corresponding summaries. These need to be linked to their
        metadata using the hashes later if needed.
    """
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT paper_hash, summary
        FROM paperprojects_table
        WHERE project_id = %s
        AND newsletter = TRUE
                   """, (project_id,))
    papers = cursor.fetchall()
    cursor.close()
    connection.close()
    return papers


def should_update(project_id: str, days_for_update: int | float) -> bool:
    """
    Return True if *either* of these are true for the given project:

    1. There are **no** rows with newsletter=True.
    2. The newest newsletter=True row is older than `days_for_update` days.

    Parameters
    ----------
    conn : psycopg2.extensions.connection
        An open connection to the database.
    project_id : str
        The project you’re checking.
    days_for_update : int | float
        Age threshold in days.

    Returns
    -------
    bool
    """
    conn = connect_to_db()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT creation_date
            FROM public.paperprojects_table
            WHERE project_id = %s
              AND newsletter IS TRUE          -- only rows flagged for the newsletter
            ORDER BY creation_date DESC
            LIMIT 1;
            """,
            (project_id,)
        )
        row = cur.fetchone()

    # No newsletter-eligible papers → definitely update
    if row is None:
        return True

    latest_date = row[0]
    # Use matching timezone if the column is tz-aware, else UTC
    now = datetime.now(latest_date.tzinfo) if latest_date.tzinfo else datetime.utcnow()
    return now - latest_date >= timedelta(days=days_for_update)


def mark_paper_seen(project_id: str, paper_hash: str) -> bool:
    """
    Mark a (project_id, paper_hash) pair as seen in paperprojects_table.

    Parameters
    ----------
    conn : psycopg2.extensions.connection
        An open psycopg2 connection.
    project_id : str
        The ID of the project.
    paper_hash : str
        The paper's hash.

    Returns
    -------
    bool
        True if one row was updated, False if no matching row existed.
    """
    conn = connect_to_db()
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE public.paperprojects_table
            SET seen = TRUE
            WHERE project_id = %s AND paper_hash = %s;
            """,
            (project_id, paper_hash)
        )
        updated = cur.rowcount  # number of rows affected

    # Commit the change—remove this if you're running with autocommit = True
    conn.commit()

    return updated == 1


def delete_project_rows(project_id: str) -> int:
    """
    Delete all rows belonging to `project_id` from public.paperprojects_table.

    Parameters
    ----------
    conn : psycopg2.extensions.connection
        An open psycopg2 connection.
    project_id : str
        The project whose rows you want to purge.

    Returns
    -------
    int
        How many rows were deleted (0 if none existed).
    """
    conn = connect_to_db()
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM public.paperprojects_table
            WHERE project_id = %s;
            """,
            (project_id,)
        )
        deleted = cur.rowcount   # rows affected

    conn.commit()               # omit if autocommit=True
    return deleted
