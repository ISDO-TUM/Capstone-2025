
import psycopg2
import psycopg2.extras
from database.database_connection import connect_to_db


def assign_paper_to_project(paper_hash: str, project_id: str, summary: str, newsletter: bool = False, seen: bool = False):
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

    cursor.execute("""INSERT INTO paperprojects_table (project_id, paper_hash, summary, newsletter, seen) VALUES (%s, %s, %s, %s, %s)""",
                   (project_id, paper_hash, summary, newsletter, seen))
    connection.commit()
    cursor.close()
    connection.close()


def get_papers_for_project(project_id: str):
    """
    Returns the list of papers for a project by linking by hash the papers from paperprojects_table
    with the ones from papers_table
    Args:
        project_id: The project's id

    Returns: A dict list where each dict contains paper metadata + a summary explaining why the paper is relevant

    """
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
            DO \
            UPDATE SET
                newsletter = EXCLUDED.newsletter, \
                seen = EXCLUDED.seen; \
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
        AND seen = FALSE
                   """, (project_id,))
    papers = cursor.fetchall()
    cursor.close()
    connection.close()
    return papers
