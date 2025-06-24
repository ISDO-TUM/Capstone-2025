
import psycopg2
import psycopg2.extras
from database.database_connection import connect_to_db


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


def get_pubsub_papers_for_project(project_id: str):
    connection = connect_to_db()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
    SELECT paper_hash from paperprojects_table
        WHERE project_id = %s
        AND newsletter = TRUE
        AND SEEN = TRUE
                   """, (project_id,))
    papers = cursor.fetchall()
    return papers
