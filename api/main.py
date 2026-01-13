from contextlib import asynccontextmanager
from fastapi import FastAPI

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

# register routes
app.include_router(migrate.router, tags=["Migrate"])
app.include_router(data.router, tags=["Data"])
app.include_router(folder.router, tags=["Folder"])
app.include_router(note.router, tags=["Note"])


@app.get("/")
def root():
    return {"status": "ok"}
