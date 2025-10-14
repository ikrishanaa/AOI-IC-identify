from fastapi import FastAPI

app = FastAPI(title="Decision Engine Service", version="0.1.0")


@app.get("/health")
def health():
    return {"service": "decision_engine", "status": "ok"}
