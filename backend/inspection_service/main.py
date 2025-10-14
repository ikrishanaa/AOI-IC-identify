from fastapi import FastAPI

app = FastAPI(title="Inspection Management Service", version="0.1.0")


@app.get("/health")
def health():
    return {"service": "inspection_service", "status": "ok"}
