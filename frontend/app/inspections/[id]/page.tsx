"use client";

import { useEffect, useState } from "react";
import VerdictBadge from "@/components/VerdictBadge";
import SignalCard from "@/components/SignalCard";
import type { InspectionJob } from "@/types/api";

export default function InspectionDetails({ params }: { params: { id: string } }) {
  const { id } = params;
  const [data, setData] = useState<InspectionJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let timer: any;
    async function tick() {
      try {
        const r = await fetch(`/api/jobs/${id}`, { cache: "no-store" });
        if (!r.ok) {
          setError(`HTTP ${r.status}: ${r.statusText}`);
          return;
        }
        const body = await r.json();
        setData(body);
        
        // Stop polling if job is complete or failed
        if (body.status === "completed" || body.status === "failed") {
          clearInterval(timer);
        }
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    tick();
    timer = setInterval(tick, 2000);
    return () => clearInterval(timer);
  }, [id]);

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: "bg-slate-100 text-slate-700 border-slate-300",
      processing: "bg-blue-50 text-blue-700 border-blue-300",
      completed: "bg-emerald-50 text-emerald-700 border-emerald-300",
      failed: "bg-rose-50 text-rose-700 border-rose-300",
    };
    return (
      <span className={`px-4 py-1.5 rounded-full text-sm font-semibold border ${colors[status] || colors.pending}`}>
        {status.toUpperCase()}
      </span>
    );
  };

  if (loading && !data) {
    return (
      <section className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-slate-200 rounded w-1/4 mb-8"></div>
          <div className="grid gap-4">
            <div className="h-32 bg-slate-200 rounded-xl"></div>
            <div className="h-32 bg-slate-200 rounded-xl"></div>
          </div>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="space-y-6">
        <h2 className="text-2xl font-bold mb-4 text-slate-800">Error</h2>
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-5 text-rose-700">
          {error}
        </div>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="space-y-6">
        <p className="text-slate-500">Inspection not found</p>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-slate-800">Inspection #{id}</h1>
          {getStatusBadge(data.status)}
        </div>
        <div className="flex gap-6 text-sm text-slate-600">
          <div>
            <span className="font-medium text-slate-500">Created:</span>{" "}
            <span className="font-medium">{new Date(data.created_at).toLocaleString()}</span>
          </div>
          {data.completed_at && (
            <div>
              <span className="font-medium text-slate-500">Completed:</span>{" "}
              <span className="font-medium">{new Date(data.completed_at).toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>

      {/* Processing State */}
      {data.status === "processing" && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <span className="text-blue-700 font-semibold">Processing inspection...</span>
          </div>
        </div>
      )}

      {/* Pending State */}
      {data.status === "pending" && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="text-slate-700 font-medium">⏳ Inspection queued for processing...</div>
        </div>
      )}

      {/* Error State */}
      {data.status === "failed" && data.error && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-rose-800 mb-2">Error</h3>
          <p className="text-rose-700">{data.error}</p>
        </div>
      )}

      {/* Results */}
      {data.result && (
        <div className="space-y-6">
          {/* Verdict Section */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-xl font-bold mb-4 text-slate-800">Final Verdict</h2>
            <div className="flex items-center gap-4 mb-4">
              <VerdictBadge verdict={data.result.verdict} confidence={data.result.confidence} />
              <div className="text-slate-600">
                Overall Score: <span className="font-bold text-lg text-slate-800">{(data.result.score * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* Verification Signals */}
          <div>
            <h2 className="text-xl font-bold mb-4 text-slate-800">Verification Signals</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              <SignalCard
                title="OCR Analysis"
                icon="📝"
                data={data.result.ocr || null}
                type="ocr"
              />
              <SignalCard
                title="Logo Detection"
                icon="🏷️"
                data={data.result.logo || null}
                type="logo"
              />
              <SignalCard
                title="Visual Signature"
                icon="🔍"
                data={data.result.visual_signature || null}
                type="visual"
              />
              <SignalCard
                title="Anomaly Detection"
                icon="⚠️"
                data={data.result.anomaly || null}
                type="anomaly"
              />
            </div>
          </div>

          {/* Decision Notes */}
          {data.result.decision_notes && data.result.decision_notes.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-xl font-bold mb-4 text-slate-800">Decision Reasoning</h2>
              <ul className="space-y-2">
                {data.result.decision_notes.map((note, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-blue-400 mt-1">•</span>
                    <span className="text-slate-700">{note}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
