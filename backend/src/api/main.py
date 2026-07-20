from fastapi import FastAPI

app = FastAPI(title="Life OS")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
