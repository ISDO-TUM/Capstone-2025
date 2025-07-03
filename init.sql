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
    counts_by_year                  JSONB,
    rating                          INTEGER
);

CREATE TABLE IF NOT EXISTS public.projects_table (
    project_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    email TEXT,
    queries TEXT
);

CREATE TABLE IF NOT EXISTS public.paperprojects_table (
    project_id TEXT NOT NULL,
    paper_hash TEXT NOT NULL,
    summary TEXT NOT NULL,
    newsletter BOOLEAN,
    PRIMARY KEY (project_id, paper_hash),
    FOREIGN KEY (project_id) REFERENCES projects_table(project_id) ON DELETE CASCADE,
    FOREIGN KEY (paper_hash) REFERENCES papers_table(paper_hash) ON DELETE CASCADE
);

-- Clear all data from the table on every startup.
TRUNCATE TABLE
    public.paperprojects_table,
    public.papers_table,
    public.projects_table
CASCADE;
