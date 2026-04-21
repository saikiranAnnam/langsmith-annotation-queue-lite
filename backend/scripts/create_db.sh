#!/bin/bash
# Helper script to create the database
# Usage: export PGPASSWORD=postgres && ./scripts/create_db.sh

psql -h localhost -U postgres -lqt | cut -d \| -f 1 | grep -qw langsmith
if [ $? -eq 0 ]; then
    echo "Database 'langsmith' already exists"
else
    psql -h localhost -U postgres -c "CREATE DATABASE langsmith;"
    echo "Database 'langsmith' created"
fi
