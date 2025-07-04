
import psycopg2
import psycopg2.extras
from database.database_connection import connect_to_db


def assign_paper_to_project(paper_hash: str, project_id: str, summary: str, is_replacement: bool = False):
    connection = connect_to_db()
    if not connection:
        raise Exception("Failed to connect to database")
    
    cursor = connection.cursor()

    try:
        # Use INSERT ... ON CONFLICT to handle duplicates
        cursor.execute("""
            INSERT INTO paperprojects_table (project_id, paper_hash, summary, is_replacement) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (project_id, paper_hash) 
            DO UPDATE SET summary = EXCLUDED.summary, is_replacement = EXCLUDED.is_replacement
        """, (project_id, paper_hash, summary, is_replacement))
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


def get_papers_for_project(project_id: str):
    connection = connect_to_db()
    if not connection:
        raise Exception("Failed to connect to database")
    
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
                   SELECT papers_table.*, paperprojects_table.rating, paperprojects_table.is_replacement
                   FROM papers_table
                   JOIN paperprojects_table ON papers_table.paper_hash = paperprojects_table.paper_hash
                   WHERE paperprojects_table.project_id = %s AND paperprojects_table.excluded = FALSE
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
    cursor.close()
    connection.close()
    return results
