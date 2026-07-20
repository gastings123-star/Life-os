from fastapi import FastAPI

from src.api.daily_planning import router as daily_planning_router

app = FastAPI(title="Life OS")
app.include_router(daily_planning_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
