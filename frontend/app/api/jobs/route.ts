import { NextResponse } from "next/server";

const INSPECTION_URL = process.env.INSPECTION_SERVICE_URL || "http://localhost:8001";

export async function POST(request: Request) {
  const body = await request.json();
  const r = await fetch(`${INSPECTION_URL}/inspections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json();
  return NextResponse.json(data, { status: r.status });
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limit = searchParams.get("limit") || "50";
  const offset = searchParams.get("offset") || "0";
  const status = searchParams.get("status");
  
  const params = new URLSearchParams({ limit, offset });
  if (status) params.append("status", status);
  
  const r = await fetch(`${INSPECTION_URL}/inspections?${params}`);
  const data = await r.json();
  return NextResponse.json(data, { status: r.status });
}
