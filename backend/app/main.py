from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (ensures models are registered before create_all)
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import assistant, family_members, recipients, tasks
from app.seed import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    yield


app = FastAPI(title="CareCircle Lite API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recipients.router)
app.include_router(family_members.router)
app.include_router(tasks.router)
app.include_router(assistant.router)


@app.get("/health")
def health():
    return {"status": "ok"}
