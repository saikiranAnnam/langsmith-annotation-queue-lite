import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.database import close_pool, get_pool
from src.jobs.requeue_stuck_entries import requeue_stuck_entries_loop
from src.routers import feedback, projects, queues, rubrics, traces

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize the connection pool
    pool = await get_pool()
    
    # Event to signal the requeue task to stop
    stop_event = asyncio.Event()
    requeue_task = None

    # Start the requeue task if enabled
    # OnCall - operator can enable/disable this feature in the future(config)
    if settings.requeue_stuck_entries_enabled:
        requeue_task = asyncio.create_task(
            requeue_stuck_entries_loop(
                pool=pool,
                interval_seconds=settings.requeue_stuck_entries_interval,
                stale_after_seconds=settings.requeue_stuck_entries_threshold,
                stop_event=stop_event,
            )
        )

    try:
        yield
    finally: 
        # Signal the requeue task to stop
        stop_event.set()
        if requeue_task is not None:
            # Wait for the requeue task to complete
            await requeue_task
        # Shutdown: close the connection pool
        await close_pool()


app = FastAPI(
    title="Annotation Queue API",
    description="API for managing annotation queues for LangSmith traces",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(traces.router)
app.include_router(queues.router)
app.include_router(rubrics.router)
app.include_router(feedback.router)


@app.get("/")
async def root():
    return {
        "message": "Annotation Queue API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
