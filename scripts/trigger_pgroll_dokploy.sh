# script to trigger pgroll command on Dokploy

export PGROLL_PG_URL="postgres://user:${DB_PASSWORD}@capstone2025-db-h2pjic:5432/papers?sslmode=disable"
pgroll init || true
echo "Running pgroll ${PGROLL_COMMAND}"
pgroll ${PGROLL_COMMAND} # set on Dokploy during CI/CD workflow
echo "Operation complete. Keeping container alive, otherwise Dokploy will keep creating new container."
echo "Note: This will consume minimal to zero CPU."
tail -f /dev/null
