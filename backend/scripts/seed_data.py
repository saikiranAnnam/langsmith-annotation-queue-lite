"""
Script to seed the database with sample data for testing the annotation queue.
"""

import asyncio
from datetime import datetime, timedelta

import asyncpg
import orjson


async def seed_database():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/langsmith")

    try:
        print("🌱 Seeding database...")

        # Get or create tracing project
        project = await conn.fetchrow("SELECT id, name FROM tracing_projects WHERE name = $1", "Sample LLM Application")

        if project:
            print(f"✓ Found existing project: {project['name']} (id={project['id']})")
        else:
            project = await conn.fetchrow(
                """
                INSERT INTO tracing_projects (name)
                VALUES ($1)
                RETURNING id, name
                """,
                "Sample LLM Application",
            )
            print(f"✓ Created project: {project['name']} (id={project['id']})")

        # Create some sample traces
        trace_data = [
            {
                "inputs": {"question": "What is the capital of France?"},
                "outputs": {"answer": "The capital of France is Paris."},
                "metadata": {"model": "gpt-4", "tokens": 25},
            },
            {
                "inputs": {"question": "Explain quantum computing in simple terms"},
                "outputs": {"answer": "Quantum computing uses quantum bits or qubits that can be in superposition..."},
                "metadata": {"model": "gpt-4", "tokens": 150},
            },
            {
                "inputs": {"question": "Write a haiku about programming"},
                "outputs": {"answer": "Code flows like water\nBugs hide in silent shadows\nTests bring clarity"},
                "metadata": {"model": "gpt-3.5-turbo", "tokens": 30},
            },
            {
                "inputs": {"question": "What is 2+2?"},
                "outputs": {"answer": "2 + 2 equals 4."},
                "metadata": {"model": "gpt-3.5-turbo", "tokens": 10},
            },
            {
                "inputs": {"question": "Tell me a joke about developers"},
                "outputs": {"answer": "Why do programmers prefer dark mode? Because light attracts bugs!"},
                "metadata": {"model": "gpt-4", "tokens": 20},
            },
        ]

        trace_ids = []
        for i, data in enumerate(trace_data):
            start_time = datetime.now() - timedelta(hours=len(trace_data) - i)
            end_time = start_time + timedelta(seconds=2)

            trace = await conn.fetchrow(
                """
                INSERT INTO traces (project_id, inputs, outputs, trace_metadata, start_time, end_time)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                project["id"],
                orjson.dumps(data["inputs"]).decode(),
                orjson.dumps(data["outputs"]).decode(),
                orjson.dumps(data["metadata"]).decode(),
                start_time,
                end_time,
            )
            trace_ids.append(trace["id"])

        print(f"✓ Created {len(trace_ids)} traces")

        # Get or create queue
        queue = await conn.fetchrow("SELECT id, name FROM queues WHERE name = $1", "Quality Review Queue")

        if queue:
            print(f"✓ Found existing queue: {queue['name']} (id={queue['id']})")
        else:
            queue = await conn.fetchrow(
                """
                INSERT INTO queues (name)
                VALUES ($1)
                RETURNING id, name
                """,
                "Quality Review Queue",
            )
            print(f"✓ Created queue: {queue['name']} (id={queue['id']})")

            # Create rubric items for the queue (only if queue is new)
            rubric_items = [
                {"feedback_key": "accuracy", "description": "Is the answer factually correct?"},
                {"feedback_key": "helpfulness", "description": "Is the answer helpful to the user?"},
                {"feedback_key": "tone", "description": "Is the tone appropriate and professional?"},
            ]

            for item in rubric_items:
                await conn.execute(
                    """
                    INSERT INTO queue_rubric_items (queue_id, feedback_key, description)
                    VALUES ($1, $2, $3)
                    """,
                    queue["id"],
                    item["feedback_key"],
                    item["description"],
                )

            print(f"✓ Created {len(rubric_items)} rubric items")

        # Populate the queue with the traces
        for trace_id in trace_ids:
            await conn.execute(
                """
                INSERT INTO queue_entries (queue_id, trace_id, status)
                VALUES ($1, $2, 'pending')
                """,
                queue["id"],
                trace_id,
            )

        print(f"✓ Added {len(trace_ids)} entries to queue")

        print("\n✨ Database seeding complete!")
        print("\nYou can now:")
        print(f"  - View the queue: GET /queues/{queue['id']}")
        print(f"  - Get next entry: GET /queues/{queue['id']}/entries/next")
        print(f"  - View rubric: GET /queues/{queue['id']}/rubric")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
