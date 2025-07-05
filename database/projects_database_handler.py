import uuid
import json
from typing import List

import psycopg2.extras

from database.database_connection import connect_to_db


def add_new_project_to_db(title: str, description: str) -> str:
    project_id = str(uuid.uuid4())
    conn = connect_to_db()
    if conn is None:
        raise Exception("Failed to connect to database")

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


def add_user_profile_embedding(project_id: str, embedding: List[float]):
    conn = connect_to_db()
    if conn is None:
        raise Exception("Failed to connect to database")

    cursor = conn.cursor()

    # Convert embedding list to JSONB format
    embedding_json = json.dumps(embedding)

    cursor.execute("""
        UPDATE projects_table
        SET user_profile_embedding = %s
        WHERE project_id = %s
    """, (embedding_json, project_id))

    conn.commit()
    cursor.close()
    conn.close()


def get_user_profile_embedding(project_id: str) -> List[float] | None:
    conn = connect_to_db()
    if conn is None:
        raise Exception("Failed to connect to database")

    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_profile_embedding
        FROM projects_table
        WHERE project_id = %s
    """, (project_id,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result and result[0]:
        # PostgreSQL JSONB is already parsed as Python object
        embedding = result[0]
        if isinstance(embedding, list):
            return embedding
        elif isinstance(embedding, str):
            # Fallback: if it's a string, parse it
            return json.loads(embedding)
        else:
            return None
    return None


def add_queries_to_project_db(queries: list[str], project_id: str):
    conn = connect_to_db()
    if conn is None:
        raise Exception("Failed to connect to database")

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


def get_all_projects() -> list[dict]:
    conn = connect_to_db()
    if conn is None:
        raise Exception("Failed to connect to database")

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("SELECT project_id, title, description FROM projects_table")

    projects = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return projects


def get_project_data(project_id: str):
    conn = connect_to_db()
    if conn is None:
        raise Exception("Failed to connect to database")

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("""
                   SELECT *
                   FROM projects_table
                   WHERE project_id = %s
                   """, (project_id,))
    result = cursor.fetchone()
    if result is None:
        return None
    project = dict(result)
    cursor.close()
    conn.close()
    return project


def add_email_to_project_db(email: str, project_id: str):
    conn = connect_to_db()
    if conn is None:
        raise Exception("Failed to connect to database")

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
