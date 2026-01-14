from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db_pool, close_db_pool
from routes import migrate, data, folder, note


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_pool()
    yield
    close_db_pool()


app = FastAPI(
    title="Note Manager API",
    description="A simple note-management system with SQL/NoSQL switch support",
    version="1.0.0",
    lifespan=lifespan,
)

import os

# Add CORS middleware for frontend
# origins from env are comma separated, e.g. "http://localhost:3000,http://localhost:8080"
origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register routes
app.include_router(migrate.router, tags=["Migrate"])
app.include_router(data.router, tags=["Data"])
app.include_router(folder.router, tags=["Folder"])
app.include_router(note.router, tags=["Note"])


@app.get("/")
def root():
    return {"status": "ok"}
