from llm.Agent import trigger_agent_show_thoughts


def create_project(project_id: str, user_query: str):
    trigger_agent_show_thoughts(user_query + "the project ID is: " + project_id)
