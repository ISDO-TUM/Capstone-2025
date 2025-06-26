
import psycopg2
import psycopg2.extras
from database.database_connection import connect_to_db
from database.papers_database_handler import get_paper_by_hash



def assign_paper_to_project(paper_hash: str, project_id: str, summary: str, newsletter: bool = False, seen: bool = False):
    connection = connect_to_db()
    cursor = connection.cursor()

    cursor.execute("""INSERT INTO paperprojects_table (project_id, paper_hash, summary) VALUES (%s, %s, %s)""",
                   (project_id, paper_hash, summary))
    connection.commit()
    cursor.close()
    connection.close()


def get_papers_for_project(project_id: str):
    connection = connect_to_db()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
                   SELECT papers_table.*
                   FROM papers_table
                            JOIN paperprojects_table ON papers_table.paper_hash = paperprojects_table.paper_hash
                   WHERE paperprojects_table.project_id = %s
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
        if summary_row:
            paper_dict['summary'] = summary_row[0]
        print(paper_dict)
        results.append(paper_dict)
    print("Successfully converted papers to dict")
    return results


def set_newsletter_tags_for_project(project_id: str, paper_hashes: list, summaries: list):
    connection = connect_to_db()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Prepare data: List of tuples (project_id, paper_hash, newsletter, seen)
    values = [(project_id, paper_hash, summary, True, False) for (paper_hash, summary) in zip(paper_hashes, summaries)]

    query = """
            INSERT INTO paperprojects_table (project_id, paper_hash, summary, newsletter, seen)
            VALUES %s ON CONFLICT (project_id, paper_hash)
            DO \
            UPDATE SET
                newsletter = EXCLUDED.newsletter, \
                seen = EXCLUDED.seen; \
            """

    psycopg2.extras.execute_values(cursor, query, values)

    connection.commit()
    cursor.close()
    connection.close()


def reset_newsletter_tags():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("""
    UPDATE paperprojects_table
    SET newsletter = FALSE,
        seen = FALSE;
    """)
    connection.commit()
    cursor.close()
    connection.close()


def get_pubsub_papers_for_project(project_id: str):
    connection = connect_to_db()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
    SELECT paper_hash from paperprojects_table
        WHERE project_id = %s
        AND newsletter = TRUE
        AND seen = FALSE
                   """, (project_id,))
    papers = cursor.fetchall()
    return papers