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
    Link a paper to a project in the paperprojects_table, with optional newsletter, seen, and replacement flags.
    Args:
        paper_hash (str): The paper's hash.
        project_id (str): The project's id.
        summary (str): Agent-generated explanation of relevance.
        newsletter (bool): If the paper belongs to pubsub/newsletter.
        seen (bool): If the paper has been seen by the user (must have newsletter=True).
        is_replacement (bool): If the paper is a replacement for a low-rated one.
    Returns:
        None
    Side effects:
        Inserts or updates a row in paperprojects_table.
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
    Retrieve the list of papers for a project, excluding pubsub papers.
    Args:
        project_id (str): The project's id.
    Returns:
        list[dict]: List of dicts with paper metadata and relevance summary.
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
    Add or update newsletter tags for a set of papers in a project.
    Args:
        project_id (str): The project's id.
        paper_hashes (list): List of paper hashes.
        summaries (list): List of paper summaries.
    Returns:
        None
    Side effects:
        Updates newsletter and seen fields in paperprojects_table.
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
    Reset the newsletter and seen tags to False for all papers in a project.
    Args:
        project_id (str): The project's id.
    Returns:
        None
    Side effects:
        Updates newsletter and seen fields in paperprojects_table.
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
    Retrieve the list of pubsub papers for a project.
    Args:
        project_id (str): The project's id.
    Returns:
        list: List of tuples (paper_hash, summary) for pubsub papers.
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
    Determine if newsletter papers for a project should be updated based on age or absence.
    Args:
        project_id (str): The project to check.
        days_for_update (int | float): Age threshold in days.
    Returns:
        bool: True if update is needed, False otherwise.
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
    Args:
        project_id (str): The project ID.
        paper_hash (str): The paper's hash.
    Returns:
        bool: True if one row was updated, False otherwise.
    Side effects:
        Updates the seen field in paperprojects_table.
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
    Delete all rows belonging to a project from paperprojects_table.
    Args:
        project_id (str): The project whose rows to delete.
    Returns:
        int: Number of rows deleted (0 if none existed).
    Side effects:
        Removes rows from paperprojects_table.
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
