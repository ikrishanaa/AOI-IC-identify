from fastapi import FastAPI

app = FastAPI(title="Component Verification Service", version="0.1.0")


@app.get("/health")
def health():
    return {"service": "verification_service", "status": "ok"}
