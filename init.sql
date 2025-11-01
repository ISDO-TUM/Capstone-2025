-- Create the table only if it doesn't already exist.
CREATE TABLE IF NOT EXISTS public.papers_table (
    paper_hash TEXT PRIMARY KEY,
    id TEXT NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT,
    publication_date TEXT,
    landing_page_url TEXT,
    pdf_url TEXT,
    similarity_score                REAL,
    fwci                            REAL,
    citation_normalized_percentile  REAL,
    cited_by_count                  INTEGER,
    counts_by_year                  JSONB
);

CREATE TABLE IF NOT EXISTS public.projects_table (
    project_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    email TEXT,
    queries TEXT,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_profile_embedding JSONB
);

CREATE TABLE IF NOT EXISTS public.users_table (
    user_id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    user_name TEXT,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS public.paperprojects_table (
    project_id TEXT NOT NULL,
    paper_hash TEXT NOT NULL,
    summary TEXT NOT NULL,
    newsletter BOOLEAN,
    seen BOOLEAN,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rating INTEGER,
    is_replacement BOOLEAN DEFAULT FALSE,
    excluded BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (project_id, paper_hash),
    FOREIGN KEY (project_id) REFERENCES projects_table(project_id) ON DELETE CASCADE,
    FOREIGN KEY (paper_hash) REFERENCES papers_table(paper_hash) ON DELETE CASCADE
);
