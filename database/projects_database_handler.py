import uuid
from database.database_connection import connect_to_db


def add_new_project_to_db(title: str, description: str) -> str:
    project_id = str(uuid.uuid4())
    conn = connect_to_db()
    cursor = conn.cursor()

    while _uuid_exists(project_id, cursor):
        project_id = str(uuid.uuid4())

    sql_insert = """
    INSERT INTO projects_table (project_id, title, description)
        VALUES (%s, %s, %s)
    """

    cursor.execute(sql_insert,
                   (project_id,
                    title,
                    description
                    ))
    conn.commit()
    cursor.close()
    conn.close()
    return project_id


def add_queries_to_project_db(queries: list[str], project_id: str):
    conn = connect_to_db()
    cursor = conn.cursor()
    queries_str = repr(queries)

    print("Updating projects_table with new queries")

    cursor.execute("""
    UPDATE projects_table SET queries = %s WHERE project_id = %s
    """, (queries_str, project_id,))
    print("Updated projects_table with new queries for project", project_id)
    conn.commit()
    cursor.close()
    conn.close()


def add_email_to_project_db(email: str, project_id: str):
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute("""
                   UPDATE projects_table
                   SET queries = %s
                   WHERE project_id = %s VALUES (%s)
                   """, (email, project_id))

    conn.commit()
    cursor.close()
    conn.close()


def _uuid_exists(project_id: str, cursor) -> bool:
    cursor.execute("SELECT 1 FROM projects_table WHERE project_id = %s", (project_id,))
    result = cursor.fetchone()

    return result is not None
