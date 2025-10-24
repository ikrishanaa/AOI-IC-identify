import { NextResponse } from "next/server";

const URLS = {
  api_gateway: process.env.API_GATEWAY_URL || "http://localhost:8003",
  inspection_service: process.env.INSPECTION_SERVICE_URL || "http://localhost:8001",
  stream_ingestion_service: process.env.STREAM_INGESTION_URL || "http://localhost:8002",
  decision_engine: process.env.DECISION_ENGINE_URL || "http://localhost:8004",
  verification_service: process.env.VERIFICATION_SERVICE_URL || "http://localhost:8005",
};

async function safeGet(url: string) {
  try {
    const r = await fetch(url, { cache: "no-store" });
    const body = await r.json().catch(() => ({}));
    return { ok: r.ok, ...body };
  } catch (e: any) {
    return { ok: false, error: e?.message || String(e) };
  }
}

export async function GET() {
  const [gw, insp, stream, dec, ver] = await Promise.all([
    safeGet(`${URLS.api_gateway}/health`),
    safeGet(`${URLS.inspection_service}/health`),
    safeGet(`${URLS.stream_ingestion_service}/health`),
    safeGet(`${URLS.decision_engine}/health`),
    safeGet(`${URLS.verification_service}/health`),
  ]);

  // also check DB for inspection_service
  const db = await safeGet(`${URLS.inspection_service}/db/health`);

  return NextResponse.json({
    api_gateway: gw,
    inspection_service: { ...insp, db: db?.db || (db.ok ? "ok" : "unknown") },
    stream_ingestion_service: stream,
    decision_engine: dec,
    verification_service: ver,
  });
}
