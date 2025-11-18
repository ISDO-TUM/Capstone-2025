# Example Migration: Adding a New Column

This example shows how to add a new column to an existing table using pgroll.

## Migration File: `02_add_keywords_column.json`

```json
{
  "name": "02_add_keywords_column",
  "operations": [
    {
      "alter_column": {
        "table": "papers_table",
        "column": "keywords",
        "type": "text[]",
        "nullable": true,
        "comment": "Array of keywords associated with the paper"
      }
    }
  ]
}
```

## To create and apply this migration:

```bash
# 1. Create the migration file
./scripts/new_migration.sh add_keywords_column

# 2. Edit migrations/02_add_keywords_column.json with the content above

# 3. Run the migration
./scripts/migrate.sh

# Or in Docker:
docker compose restart web
```

## Other Common Migration Examples

### Adding an Index
```json
{
  "name": "03_add_title_index",
  "operations": [
    {
      "sql": {
        "up": "CREATE INDEX idx_papers_title ON papers_table USING gin(to_tsvector('english', title));",
        "down": "DROP INDEX IF EXISTS idx_papers_title;"
      }
    }
  ]
}
```

### Adding a Foreign Key
```json
{
  "name": "04_add_author_table",
  "operations": [
    {
      "create_table": {
        "name": "authors_table",
        "columns": [
          {"name": "author_id", "type": "text", "pk": true},
          {"name": "name", "type": "text", "nullable": false},
          {"name": "affiliation", "type": "text", "nullable": true}
        ]
      }
    },
    {
      "sql": {
        "up": "ALTER TABLE papers_table ADD COLUMN author_id text REFERENCES authors_table(author_id);"
      }
    }
  ]
}
```

### Modifying Column Type
```json
{
  "name": "05_change_rating_type",
  "operations": [
    {
      "sql": {
        "up": "ALTER TABLE paperprojects_table ALTER COLUMN rating TYPE smallint;",
        "down": "ALTER TABLE paperprojects_table ALTER COLUMN rating TYPE integer;"
      }
    }
  ]
}
```

For more examples and documentation, see: https://github.com/xataio/pgroll#operations
