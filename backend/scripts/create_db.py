"""
Script to automatically create the langsmith database if it doesn't exist.
"""

import asyncio
import sys

import asyncpg


async def create_database():
    """Create the langsmith database if it doesn't exist."""
    db_name = "langsmith"

    try:
        # Connect to the default 'postgres' database
        conn = await asyncpg.connect(
            host="localhost", port=5432, user="postgres", password="postgres", database="postgres"
        )

        try:
            # Check if database exists
            result = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)

            if result:
                print(f"✓ Database '{db_name}' already exists")
            else:
                # Create the database
                await conn.execute(f'CREATE DATABASE "{db_name}"')
                print(f"✓ Created database '{db_name}'")
        finally:
            await conn.close()

    except asyncpg.InvalidPasswordError:
        print("❌ Error: Invalid password for user 'postgres'")
        print("   Please ensure PostgreSQL is running and the password is correct")
        sys.exit(1)
    except asyncpg.PostgresConnectionError as e:
        print(f"❌ Error: Could not connect to PostgreSQL: {e}")
        print("   Please ensure PostgreSQL is running on localhost:5432")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_database())
