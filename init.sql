-- Create the table only if it doesn't already exist.
CREATE TABLE IF NOT EXISTS public.papers_table (
    paper_hash TEXT PRIMARY KEY,
    id TEXT NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT,
    publication_date TEXT,
    landing_page_url TEXT,
    pdf_url TEXT
);

CREATE TABLE IF NOT EXISTS public.projects_table (
    project_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    email TEXT,
    queries TEXT
);

CREATE TABLE IF NOT EXISTS public.paperprojects_table (
    project_id TEXT PRIMARY KEY,
    paper_hash TEXT NOT NULL,
    newsletter BOOLEAN
);

-- Clear all data from the table on every startup.
TRUNCATE TABLE public.papers_table;
TRUNCATE TABLE public.projects_table;
TRUNCATE TABLE public.paperprojects_table;
