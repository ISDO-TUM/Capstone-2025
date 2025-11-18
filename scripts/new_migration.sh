#!/bin/bash
set -e

# Migration name from argument
MIGRATION_NAME=$1

if [ -z "$MIGRATION_NAME" ]; then
  echo "Usage: ./scripts/new_migration.sh <migration_name>"
  echo "Example: ./scripts/new_migration.sh add_user_preferences"
  exit 1
fi

# Get the next migration number
LAST_MIGRATION=$(ls -1 migrations/*.json 2>/dev/null | sort -V | tail -n 1 | sed 's/.*\/\([0-9]*\)_.*/\1/')
if [ -z "$LAST_MIGRATION" ]; then
  NEXT_NUM="02"
else
  NEXT_NUM=$(printf "%02d" $((10#$LAST_MIGRATION + 1)))
fi

MIGRATION_FILE="migrations/${NEXT_NUM}_${MIGRATION_NAME}.json"

# Create migration template WITHOUT "name" field (pgroll doesn't support it)
cat > "$MIGRATION_FILE" << 'EOF'
{
  "operations": [
    {
      "sql": {
        "up": "-- Add your SQL migration here\n-- Example: ALTER TABLE papers_table ADD COLUMN new_field text;",
        "down": "-- Add rollback SQL here (optional)\n-- Example: ALTER TABLE papers_table DROP COLUMN new_field;"
      }
    }
  ]
}
EOF

echo "Created migration: $MIGRATION_FILE"
echo ""
echo "Common Operation Examples:"
echo ""
echo "1. Add Column (SQL):"
echo "   {\"sql\": {\"up\": \"ALTER TABLE papers_table ADD COLUMN tags text[];\"}}"
echo ""
echo "2. Create Index (SQL):"
echo "   {\"sql\": {\"up\": \"CREATE INDEX idx_papers_title ON papers_table(title);\"}}"
echo ""
echo "3. Declarative Add Column:"
echo "   {\"alter_column\": {\"table\": \"papers_table\", \"column\": \"new_field\", \"type\": \"text\", \"nullable\": true}}"
echo ""
echo "4. Create New Table:"
echo "   {\"create_table\": {\"name\": \"new_table\", \"columns\": [...]}}"
echo ""
echo "Full docs: https://github.com/xataio/pgroll#operations"
echo ""
echo "Next steps:"
echo "   1. Edit: $MIGRATION_FILE"
echo "   2. Test: ./scripts/migrate.sh"
echo "   3. Commit: git add $MIGRATION_FILE && git commit -m 'Add migration: $MIGRATION_NAME'"
