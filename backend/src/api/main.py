from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.daily_planning import actions_router
from src.api.daily_planning import router as daily_planning_router

app = FastAPI(title="Life OS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(daily_planning_router)
app.include_router(actions_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
