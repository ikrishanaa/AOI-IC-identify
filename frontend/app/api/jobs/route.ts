import { NextResponse } from "next/server";

const INSPECTION_URL = process.env.INSPECTION_SERVICE_URL || "http://localhost:8001";

export async function POST() {
  const r = await fetch(`${INSPECTION_URL}/debug/jobs`, { method: "POST" });
  const body = await r.json();
  return NextResponse.json(body, { status: r.status });
}
