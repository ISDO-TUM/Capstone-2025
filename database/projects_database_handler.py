import uuid
import psycopg2.extras
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
                    description,
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


def get_queries_for_project(project_id: str):
    # conn = connect_to_db(outside_chroma=True)
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute(""" SELECT queries FROM projects_table WHERE project_id = %s""", (project_id,))

    queries = cursor.fetchone()
    return queries


def get_project_prompt(project_id: str):
    conn = connect_to_db()
    # conn = connect_to_db(outside_chroma=True)
    cursor = conn.cursor()

    cursor.execute(""" SELECT description
                       FROM projects_table
                       WHERE project_id = %s""", (project_id,))

    prompt = cursor.fetchone()
    return prompt


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


def get_project_by_id(project_id: str):
    """
    Returns a dict with all fields from row projects_table
    or None if it does not exist.
    """
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
        SELECT project_id, title, description, email, queries
          FROM projects_table
         WHERE project_id = %s
    """, (project_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None
