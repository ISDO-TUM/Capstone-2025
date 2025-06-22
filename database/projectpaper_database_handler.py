from database.database_connection import connect_to_db


def assign_paper_to_project(paper_hash: str, project_id: str, summary: str):
    connection = connect_to_db()
    cursor = connection.cursor()

    cursor.execute(f"INSERT INTO paperprojects_table (project_id, paper_hash, summary) VALUES (%s, %s, %s)",
                   (project_id, paper_hash, summary))
    connection.commit()
    cursor.close()
    connection.close()


def get_papers_for_project(project_id: str):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("""
                   SELECT papers_table.*
                   FROM papers_table
                            JOIN paperprojects_table ON papers_table.id = paperprojects_table.paper_hash
                   WHERE paperprojects_table.project_id = %s
                   """, (project_id,))
    papers = cursor.fetchall()

    result = [dict(row) for row in papers]
    return result
