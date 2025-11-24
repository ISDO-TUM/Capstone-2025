# Database Migrations Guide

This project uses [pgroll](https://github.com/xataio/pgroll) for zero-downtime PostgreSQL schema migrations.

## Overview

pgroll provides:
- **Zero-downtime migrations**: Schema changes without service interruption
- **Version control**: All schema changes tracked in JSON migration files
- **Rollback support**: Easy migration reversal if needed
- **Docker integration**: Seamless operation in containerized environments

## Running Migrations

### In Docker (Automatic)

Migrations run automatically when you start the container:
```bash
docker compose up -d
```

The web service will automatically:
1. Initialize pgroll (if not already initialized)
2. Apply all migrations in `migrations/` directory in sequential order
3. Complete each migration before moving to the next

### Manually in Docker

```bash
# Run all pending migrations
docker compose exec web pgroll migrate

# Check migration status
docker compose exec web pgroll status

# View migration history
docker compose logs web | grep migration
```

### Local Development

If you have pgroll installed locally:

```bash
# Install pgroll (macOS)
brew install xataio/tap/pgroll

# Or download binary from: https://github.com/xataio/pgroll/releases

# Run all migrations
pgroll migrate

# Or use the helper script
../scripts/migrate.sh

# Check migration status
../scripts/migration_status.sh
```

## Creating New Migrations

### 1. Generate a Migration File

```bash
../scripts/new_migration.sh add_user_preferences
```

This creates a new migration file in `migrations/` with the next sequential number.

### 2. Edit the Migration File

Add your schema changes to the generated file.

**Example - Adding a column:**
```json
{
  "name": "02_add_user_preferences",
  "operations": [
    {
      "alter_column": {
        "table": "projects_table",
        "column": "user_preferences",
        "type": "jsonb",
        "nullable": true,
        "comment": "Store user-specific preferences"
      }
    }
  ]
}
```

**Example - Creating an index:**
```json
{
  "name": "03_add_paper_index",
  "operations": [
    {
      "sql": {
        "up": "CREATE INDEX idx_papers_publication_date ON papers_table(publication_date);",
        "down": "DROP INDEX IF EXISTS idx_papers_publication_date;"
      }
    }
  ]
}
```

### 3. Run the Migration

```bash
# In Docker (recommended)
docker compose exec web pgroll migrate

# Or restart the container (migrations run on startup)
docker compose restart web

# Or manually with local pgroll
../scripts/migrate.sh
```

## Available Migration Operations

pgroll supports various operations:
- `create_table`: Create new tables
- `drop_table`: Remove tables
- `alter_column`: Add/modify/remove columns
- `create_index`: Add indexes
- `sql`: Execute raw SQL (with optional rollback for `down` migrations)

For complete documentation, see [pgroll operations guide](https://github.com/xataio/pgroll#operations).

## Migration Files Structure

All migrations are stored in the `migrations/` directory:
```
migrations/
├── 01_initial_schema.json       # Initial database schema
├── README.md                    # This file
└── EXAMPLE.md                   # Migration examples and templates
```

**Important Notes:**
- Migration files are applied in **alphabetical/numerical order**
- Once a migration is applied, **do not modify** the migration file
- Each migration file should contain a single logical schema change
- Use descriptive names for migration files (e.g., `03_add_citations_index.json`)

## Helper Scripts

Located in `../scripts/`:

### migrate.sh - Run all pending migrations
```bash
../scripts/migrate.sh
```
This script:
- Initializes pgroll if needed
- Applies all migrations in order
- Shows detailed progress for each migration

### new_migration.sh - Create a new migration file
```bash
../scripts/new_migration.sh add_feature_name
```
Generates a numbered migration file with a template

### migration_status.sh - Check current migration status
```bash
../scripts/migration_status.sh
```
Shows applied migrations and database state

## Configuration

pgroll is configured via `../pgroll.json`:
```json
{
  "pg_url": "postgres://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?sslmode=disable",
  "schema": "public",
  "migrations_dir": "migrations"
}
```

Environment variables are automatically injected from `.env` or Docker environment.

**Required Environment Variables:**
- `DB_HOST` - PostgreSQL host (default: `localhost`)
- `DB_PORT` - PostgreSQL port (default: `5432`)
- `DB_NAME` - Database name (default: `papers`)
- `DB_USER` - Database user (default: `user`)
- `DB_PASSWORD` - Database password (required)

## Troubleshooting

### Migration fails to start

```bash
# Check pgroll status
docker compose exec web pgroll status

# View container logs
docker compose logs web | grep -i migration

# Check database connection
docker compose exec web psql -U $DB_USER -d $DB_NAME -c "\dt"
```

### Duplicate column error

**Error:** `column "column_name" already exists`

This usually means:
1. A migration was already applied manually or by a previous run
2. The migration file is trying to add a column that exists

**Solution:**
```bash
# Option 1: Remove the duplicate migration file if it's incorrect
rm migrations/XX_duplicate_migration.json

# Option 2: Check which migrations are applied
docker compose exec web pgroll status

# Option 3: Reset and restart (!destructive! - only for development)
docker compose down -v
docker compose up -d
```

### Migration state mismatch

If you modify a migration file after it's been applied, you'll get errors like the duplicate column error above.

**Why this happens:**
1. You run migrations → Migration is applied to database → State is recorded
2. You modify the migration file → File content changes
3. You run migrations again → System tries to re-apply modified migration
4. **Error:** Database already has the changes from step 1

**Solution:**
Never modify applied migrations. Instead:
- Create a new migration file for changes
- Or reset the database completely (development only)

### Reset migrations (!destructive! - development only)

```bash
# This will drop all tables and re-run migrations from scratch
docker compose down -v  # Remove volumes
docker compose up -d    # Restart and re-apply all migrations
```

### Rollback a migration

```bash
# Rollback the last migration
docker compose exec web pgroll rollback

# Or use the down SQL if provided in the migration
```

### Check if a specific migration was applied

```bash
# View migration history in logs
docker compose logs web | grep "Migration.*completed"

# Or check database directly
docker compose exec web psql -U $DB_USER -d $DB_NAME -c "\d your_table_name"
```

## Common Migration Patterns

### Adding a new column with default value

```json
{
  "name": "add_is_featured_column",
  "operations": [
    {
      "alter_column": {
        "table": "papers_table",
        "column": "is_featured",
        "type": "boolean",
        "nullable": false,
        "default": "false"
      }
    }
  ]
}
```

### Creating a foreign key

```json
{
  "name": "add_user_foreign_key",
  "operations": [
    {
      "sql": {
        "up": "ALTER TABLE paperprojects_table ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users_table(user_id) ON DELETE CASCADE;",
        "down": "ALTER TABLE paperprojects_table DROP CONSTRAINT fk_user;"
      }
    }
  ]
}
```

### Adding a full-text search index

```json
{
  "name": "add_title_fts_index",
  "operations": [
    {
      "sql": {
        "up": "CREATE INDEX idx_papers_title_fts ON papers_table USING gin(to_tsvector('english', title));",
        "down": "DROP INDEX IF EXISTS idx_papers_title_fts;"
      }
    }
  ]
}
```

### Adding multiple columns in one migration

```json
{
  "name": "add_paper_metadata",
  "operations": [
    {
      "alter_column": {
        "table": "papers_table",
        "column": "doi",
        "type": "text",
        "nullable": true
      }
    },
    {
      "alter_column": {
        "table": "papers_table",
        "column": "keywords",
        "type": "text[]",
        "nullable": true
      }
    }
  ]
}
```

For more examples, see [EXAMPLE.md](EXAMPLE.md).

## Best Practices

1. **One logical change per migration** - Keep migrations focused and atomic
2. **Never modify applied migrations** - Create new migrations for changes
3. **Always include `down` SQL for rollbacks** - Especially for raw SQL operations
4. **Test migrations locally first** - Use `docker compose down -v && docker compose up` to test from scratch
5. **Use descriptive migration names** - Make it clear what the migration does
6. **Document complex migrations** - Add comments in the JSON explaining why changes are needed
7. **Check migration status before and after** - Verify migrations applied correctly

## Additional Resources

- [pgroll GitHub Repository](https://github.com/xataio/pgroll)
- [pgroll Operations Documentation](https://github.com/xataio/pgroll#operations)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
