import { NextResponse } from "next/server";

const INSPECTION_URL = process.env.INSPECTION_SERVICE_URL || "http://localhost:8001";

export async function GET(
  _req: Request,
  { params }: { params: { id: string } }
) {
  const r = await fetch(`${INSPECTION_URL}/debug/jobs/${params.id}`);
  const body = await r.json();
  return NextResponse.json(body, { status: r.status });
}
