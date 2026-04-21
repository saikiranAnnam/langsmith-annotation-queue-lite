from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import close_pool, get_pool
from src.routers import feedback, projects, queues, rubrics, traces


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize the connection pool
    await get_pool()
    yield
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
