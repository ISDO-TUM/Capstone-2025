import logging
import uuid
import json
from typing import List

import psycopg2.extras
from utils.status import Status
from database.database_connection import connect_to_db

logger = logging.getLogger(__name__)


def add_new_project_to_db(title: str, description: str) -> str:
    """
    Adds a new project to projects_table
    Args:
        title: project title
        description: project description

    Returns: void

    """
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
    """
    Adds search queries to projects_table so that we can reuse them to prevent calling the agent
    to generate them again
    Args:
        queries: search queries for papers related to the project
        project_id: the project id

    Returns: operation status

    """
    conn = connect_to_db()
    cursor = conn.cursor()
    queries_str = repr(queries)

    logger.info("Updating projects_table with new queries")

    try:
        cursor.execute("""
        UPDATE projects_table SET queries = %s WHERE project_id = %s
        """, (queries_str, project_id,))
    except Exception as e:
        logger.error(f"Error updating projects_table with project queries: {e}")
        conn.rollback()
        return Status.FAILURE

    logger.info(f"Updated projects_table with new queries for project {project_id}")
    conn.commit()
    cursor.close()
    conn.close()
    return Status.SUCCESS


def get_queries_for_project(project_id: str):
    """
    Returns the list of paper API search queries for a project
    Args:
        project_id: the project id
    """
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute(""" SELECT queries FROM projects_table WHERE project_id = %s""", (project_id,))

    queries = cursor.fetchone()
    return queries


def get_project_prompt(project_id: str):
    """
    Returns the project description for the given project
    Args:
        project_id: the project's id
    """
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute(""" SELECT description
                       FROM projects_table
                       WHERE project_id = %s""", (project_id,))

    prompt = cursor.fetchone()
    return prompt


def get_all_projects() -> list[dict]:
    """
    Returns a list of all projects
    """
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("SELECT project_id, title, description, creation_date FROM projects_table")

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
    """
    Adds an email to a project so that we can send newsletter mails with pubsub papers to it
    """
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
    """
    Checks if a project with a certain uuid exists.
    Args:
        project_id: the UUID of the project
        cursor: cursor to query the projects_table

    Returns:
        True if a project with uuid exists

    """
    cursor.execute("SELECT 1 FROM projects_table WHERE project_id = %s", (project_id,))
    result = cursor.fetchone()

    return result is not None


def get_project_by_id(project_id: str):
    """
    Returns a dict with all fields from the row with the project_id = 'project_id' from
    the projects_table or None if it does not exist.
    """
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
        SELECT *
          FROM projects_table
         WHERE project_id = %s
    """, (project_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None
