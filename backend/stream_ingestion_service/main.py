from fastapi import FastAPI, WebSocket
from fastapi.responses import PlainTextResponse

app = FastAPI(title="Stream Ingestion & Processing Service", version="0.1.0")


@app.get("/health")
def health():
    return {"service": "stream_ingestion_service", "status": "ok"}


@app.get("/live/feed")
def live_feed_stub():
    return PlainTextResponse("Live feed not implemented yet", status_code=501)


@app.websocket("/ws/live/analysis")
async def ws_live_analysis(ws: WebSocket):
    await ws.accept()
    await ws.send_json({"message": "live analysis stub", "service": "stream_ingestion_service"})
    await ws.close()
