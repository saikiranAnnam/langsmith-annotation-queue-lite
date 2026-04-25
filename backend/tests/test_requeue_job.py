"""Tests for the requeue stuck entries background job."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from src.jobs.requeue_stuck_entries import requeue_stuck_entries, requeue_stuck_entries_loop


class MockPool:
    """Wraps a test db_conn as a pool so requeue_stuck_entries can call pool.acquire()."""

    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return self

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *args):
        pass


async def test_requeue_stuck_entries_requeues_stale_entry(db_conn, sample_queue_entry):
    """Stuck in_progress entries older than threshold are reset to pending."""
    stale_reserved_at = datetime.now(UTC) - timedelta(minutes=5)
    await db_conn.execute(
        """
        UPDATE queue_entries
        SET status = 'in_progress',
            reserved_at = $1,
            reserved_by = 'test-user'
        WHERE id = $2
        """,
        stale_reserved_at,
        sample_queue_entry["id"],
    )

    count = await requeue_stuck_entries(MockPool(db_conn), stale_after_seconds=60)

    assert count == 1

    row = await db_conn.fetchrow(
        "SELECT status, reserved_at, reserved_by FROM queue_entries WHERE id = $1",
        sample_queue_entry["id"],
    )
    assert row["status"] == "pending"
    assert row["reserved_at"] is None
    assert row["reserved_by"] is None


async def test_requeue_stuck_entries_ignores_fresh_entry(db_conn, sample_queue_entry):
    """in_progress entries reserved recently are not requeued."""
    await db_conn.execute(
        """
        UPDATE queue_entries
        SET status = 'in_progress',
            reserved_at = NOW(),
            reserved_by = 'test-user'
        WHERE id = $1
        """,
        sample_queue_entry["id"],
    )

    count = await requeue_stuck_entries(MockPool(db_conn), stale_after_seconds=1800)

    assert count == 0

    row = await db_conn.fetchrow(
        "SELECT status FROM queue_entries WHERE id = $1",
        sample_queue_entry["id"],
    )
    assert row["status"] == "in_progress"


async def test_requeue_stuck_entries_returns_zero_when_nothing_stuck(db_conn, sample_queue_entry):
    """Returns 0 when no stuck entries exist."""
    count = await requeue_stuck_entries(MockPool(db_conn), stale_after_seconds=60)
    assert count == 0


async def test_requeue_stuck_entries_loop_stops_on_event():
    """Loop exits cleanly when stop_event is set before it starts."""
    stop_event = asyncio.Event()
    stop_event.set()

    with patch(
        "src.jobs.requeue_stuck_entries.requeue_stuck_entries",
        new=AsyncMock(return_value=0),
    ) as mock_job:
        await requeue_stuck_entries_loop(
            pool=object(),
            interval_seconds=60,
            stale_after_seconds=1800,
            stop_event=stop_event,
        )

    mock_job.assert_not_called()


async def test_requeue_stuck_entries_loop_continues_on_exception():
    """Loop does not crash when the job raises an exception."""
    stop_event = asyncio.Event()
    call_count = 0

    async def flaky_job(pool, stale_after_seconds):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("DB connection lost")
        stop_event.set()
        return 0

    with patch("src.jobs.requeue_stuck_entries.requeue_stuck_entries", new=flaky_job):
        await requeue_stuck_entries_loop(
            pool=object(),
            interval_seconds=0,
            stale_after_seconds=1800,
            stop_event=stop_event,
        )

    assert call_count == 2
