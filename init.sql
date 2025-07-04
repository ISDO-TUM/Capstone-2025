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

-- Clear all data from the table on every startup.
TRUNCATE TABLE public.papers_table;
