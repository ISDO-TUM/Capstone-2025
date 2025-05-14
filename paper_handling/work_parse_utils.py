def strip_openalex_id(openalex_url):
    """
    Extracts the OpenAlex ID from a full OpenAlex URL.

    Example:
        "https://openalex.org/W2741809807" → "W2741809807"
    """
    if not openalex_url:
        return None
    return openalex_url.rsplit("/", 1)[-1]


# todo strip the author id
def get_authors_and_ids(work):
    authors = work['authorships']
    author_list = []

    for author in authors:
        name = author["author"].get("display_name", "Unknown Author")
        author_id = author["author"].get("id", "Unknown ID")
        author_list.append(f"{name} ({author_id})")

    return "; ".join(author_list)
