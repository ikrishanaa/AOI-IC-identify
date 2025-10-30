import { NextResponse } from "next/server";

const INSPECTION_URL = process.env.INSPECTION_SERVICE_URL || "http://localhost:8001";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const inspectionType = searchParams.get("inspection_type");

  const url = new URL(`${INSPECTION_URL}/history`);
  if (inspectionType) url.searchParams.set("inspection_type", inspectionType);

  const r = await fetch(url.toString(), { cache: "no-store" });
  const data = await r.json();
  return NextResponse.json(data, { status: r.status });
}