#!/bin/bash

# Database initialization script for AI Cloud Storage
# This script initializes the database with schema and seed data

set -e

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Default database connection parameters
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-"aicloud"}
DB_USER=${DB_USER:-"aicloud"}
DB_PASSWORD=${DB_PASSWORD:-"aicloud"}

# Function to check if PostgreSQL is ready
wait_for_postgres() {
    echo "Waiting for PostgreSQL to be ready..."
    until docker exec aicloud-postgres pg_isready -U "$DB_USER" 2>/dev/null; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 1
    done
    echo "PostgreSQL is up and running!"
}

# Function to initialize the database
initialize_database() {
    echo "Initializing database..."
    docker cp init.sql aicloud-postgres:/tmp/init.sql
    docker exec aicloud-postgres psql -U "$DB_USER" -d "$DB_NAME" -f /tmp/init.sql
    if [ $? -eq 0 ]; then
        echo "Database initialization completed successfully!"
    else
        echo "Error: Database initialization failed!"
        exit 1
    fi
}

# Main execution
echo "Starting database initialization process..."

# Wait for PostgreSQL to be ready
wait_for_postgres

# Initialize database
initialize_database

echo "Database setup process completed!"
