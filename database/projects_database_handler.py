"""
This module handles all project-related database operations for the Capstone project.

Responsibilities:
- Creating, updating, and deleting project records
- Managing project metadata, queries, and user profile embeddings
- Fetching project data and queries for recommendation flows

All project operations are designed to be robust, transactional, and reusable by the agent and API layers.
"""

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
    Add a new project to the projects_table.
    Args:
        title (str): Project title.
        description (str): Project description.
    Returns:
        str: The generated project_id for the new project.
    Side effects:
        Inserts a new row into the projects_table in the database.
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
    """
    Add or update the user profile embedding for a project in the database.
    Args:
        project_id (str): The project ID.
        embedding (list[float]): The embedding vector to store.
    Returns:
        None
    Side effects:
        Updates the user_profile_embedding field in the projects_table.
    """
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
    """
    Retrieve the user profile embedding for a project.
    Args:
        project_id (str): The project ID.
    Returns:
        list[float] or None: The embedding vector, or None if not found.
    """
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
    Add search queries to a project in the projects_table for reuse.
    Args:
        queries (list[str]): List of search queries.
        project_id (str): The project ID.
    Returns:
        Status: Status.SUCCESS if update was successful, Status.FAILURE otherwise.
    Side effects:
        Updates the queries field in the projects_table.
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
    Retrieve the list of paper API search queries for a project.
    Args:
        project_id (str): The project ID.
    Returns:
        list or None: The list of queries, or None if not found.
    """
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute(""" SELECT queries FROM projects_table WHERE project_id = %s""", (project_id,))

    queries = cursor.fetchone()
    return queries


def get_project_prompt(project_id: str):
    """
    Retrieve the project description (prompt) for the given project.
    Args:
        project_id (str): The project ID.
    Returns:
        str or None: The project description, or None if not found.
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
    Retrieve a list of all projects in the database.
    Returns:
        list[dict]: List of all project records as dictionaries.
    """
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("SELECT project_id, title, description, creation_date FROM projects_table")

    projects = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return projects


def get_project_data(project_id: str):
    """
    Retrieve all data for a project by its project_id.
    Args:
        project_id (str): The project ID.
    Returns:
        dict or None: Dictionary of project data, or None if not found.
    """
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
    Add an email to a project for newsletter mailings.
    Args:
        email (str): The email address to add.
        project_id (str): The project ID.
    Returns:
        None
    Side effects:
        Updates the queries field in the projects_table (may be a bug, check logic).
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
    Check if a project with a certain UUID exists in the database.
    Args:
        project_id (str): The UUID of the project.
        cursor: Database cursor to query the projects_table.
    Returns:
        bool: True if a project with the UUID exists, False otherwise.
    """
    cursor.execute("SELECT 1 FROM projects_table WHERE project_id = %s", (project_id,))
    result = cursor.fetchone()

    return result is not None


def get_project_by_id(project_id: str):
    """
    Retrieve all fields for a project by its project_id.
    Args:
        project_id (str): The project ID.
    Returns:
        dict or None: Dictionary of project data, or None if not found.
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


def update_project_description(project_id: str, new_description: str):
    """
    Update the project description (prompt) for the given project_id.
    Args:
        project_id (str): The project ID.
        new_description (str): The new project description.
    Returns:
        Status: Status.SUCCESS if update was successful, Status.FAILURE otherwise.
    Side effects:
        Updates the description field in the projects_table.
    """
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE projects_table
            SET description = %s
            WHERE project_id = %s
        """, (new_description, project_id))
        conn.commit()
        status = Status.SUCCESS
    except Exception as e:
        logger.error(f"Error updating project description: {e}")
        conn.rollback()
        status = Status.FAILURE
    cursor.close()
    conn.close()
    return status
