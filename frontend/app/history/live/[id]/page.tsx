"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import VerdictBadge from "@/components/VerdictBadge";

type LiveRunDetails = {
  id: number;
  camera_source: string;
  status: string;
  started_at: string;
  ended_at?: string;
  total_frames: number;
  frames_analyzed: number;
  pass_count: number;
  fail_count: number;
  review_count: number;
  frames?: FrameResult[];
};

type FrameResult = {
  frame_id: number;
  verdict: "pass" | "fail" | "needs_review";
  confidence: number;
  ocr_text?: string;
  logo_manufacturer?: string;
  timestamp: string;
};

export default function LiveInspectionDetailPage() {
  const router = useRouter();
  const params = useParams();
  const runId = params?.id as string;

  const [details, setDetails] = useState<LiveRunDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showFrames, setShowFrames] = useState(false);

  useEffect(() => {
    if (runId) {
      fetchDetails();
    }
  }, [runId]);

  const fetchDetails = async () => {
    setLoading(true);
    setError("");
    try {
      const url = new URL(`http://localhost:8001/live/runs/${runId}`);
      url.searchParams.append("include_frames", "true");

      const res = await fetch(url.toString());
      if (!res.ok) throw new Error("Failed to fetch details");

      const data = await res.json();
      setDetails(data);
    } catch (err: any) {
      setError(`Failed to load details: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const getDuration = () => {
    if (!details?.started_at) return "N/A";
    const start = new Date(details.started_at);
    const end = details.ended_at ? new Date(details.ended_at) : new Date();
    const diffMs = end.getTime() - start.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffSecs = Math.floor((diffMs % 60000) / 1000);
    return `${diffMins}m ${diffSecs}s`;
  };

  if (loading) {
    return (
      <section className="space-y-6">
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center">
          <div className="text-4xl mb-3">⏳</div>
          <p className="text-slate-600">Loading inspection details...</p>
        </div>
      </section>
    );
  }

  if (error || !details) {
    return (
      <section className="space-y-6">
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-8 text-center">
          <div className="text-4xl mb-3">❌</div>
          <h3 className="text-xl font-semibold text-rose-800 mb-2">Error</h3>
          <p className="text-rose-600">{error || "Inspection not found"}</p>
          <button
            onClick={() => router.push("/history")}
            className="mt-4 px-6 py-2 bg-rose-600 text-white rounded-lg font-semibold hover:bg-rose-700"
          >
            ← Back to History
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => router.push("/history")}
              className="text-slate-600 hover:text-slate-800 font-medium"
            >
              ← Back
            </button>
            <span className="text-slate-300">|</span>
            <span className="px-3 py-1 bg-teal-100 text-teal-700 rounded-full text-xs font-semibold uppercase">
              LIVE
            </span>
            <span className="text-slate-500 text-sm font-mono">Run #{details.id}</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-800">Live Inspection Details</h1>
        </div>
      </div>

      {/* Summary Card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Summary</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {/* Status */}
          <div className="bg-slate-50 rounded-lg p-4">
            <div className="text-xs text-slate-500 mb-1">Status</div>
            <div className="text-2xl font-bold text-slate-800">{details.status}</div>
          </div>

          {/* Duration */}
          <div className="bg-slate-50 rounded-lg p-4">
            <div className="text-xs text-slate-500 mb-1">Duration</div>
            <div className="text-2xl font-bold text-slate-800">{getDuration()}</div>
          </div>

          {/* Frames Analyzed */}
          <div className="bg-slate-50 rounded-lg p-4">
            <div className="text-xs text-slate-500 mb-1">Frames Analyzed</div>
            <div className="text-2xl font-bold text-slate-800">
              {details.frames_analyzed} / {details.total_frames}
            </div>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-slate-200">
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-slate-500">Camera Source:</span>{" "}
              <span className="text-slate-800 font-mono">{details.camera_source}</span>
            </div>
            <div>
              <span className="text-slate-500">Started:</span>{" "}
              <span className="text-slate-800 font-medium">
                {formatDate(details.started_at)}
              </span>
            </div>
            {details.ended_at && (
              <div>
                <span className="text-slate-500">Ended:</span>{" "}
                <span className="text-slate-800 font-medium">
                  {formatDate(details.ended_at)}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Results Overview */}
      <div className="bg-white border border-slate-200 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Results Overview</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-5 text-center">
            <div className="text-4xl font-bold text-emerald-600 mb-1">
              {details.pass_count}
            </div>
            <div className="text-sm font-medium text-emerald-700">PASS</div>
          </div>

          <div className="bg-rose-50 border border-rose-200 rounded-lg p-5 text-center">
            <div className="text-4xl font-bold text-rose-600 mb-1">
              {details.fail_count}
            </div>
            <div className="text-sm font-medium text-rose-700">FAIL</div>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-lg p-5 text-center">
            <div className="text-4xl font-bold text-amber-600 mb-1">
              {details.review_count}
            </div>
            <div className="text-sm font-medium text-amber-700">NEEDS REVIEW</div>
          </div>
        </div>
      </div>

      {/* Frame Results */}
      {details.frames && details.frames.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-800">
              Frame Analysis Results ({details.frames.length})
            </h2>
            <button
              onClick={() => setShowFrames(!showFrames)}
              className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-colors"
            >
              {showFrames ? "Hide Frames" : "Show All Frames"}
            </button>
          </div>

          {showFrames && (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {details.frames.map((frame) => (
                <div
                  key={frame.frame_id}
                  className="bg-slate-50 border border-slate-200 rounded-lg p-4 hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="text-sm">
                        <span className="text-slate-500">Frame</span>{" "}
                        <span className="font-mono font-bold text-slate-800">
                          #{frame.frame_id}
                        </span>
                      </div>
                      <VerdictBadge
                        verdict={frame.verdict}
                        confidence={frame.confidence}
                        className="text-sm"
                      />
                    </div>
                    <div className="text-xs text-slate-500">
                      {formatDate(frame.timestamp)}
                    </div>
                  </div>
                  {(frame.ocr_text || frame.logo_manufacturer) && (
                    <div className="mt-3 flex gap-4 text-sm">
                      {frame.ocr_text && (
                        <div>
                          <span className="text-slate-500">OCR:</span>{" "}
                          <span className="font-mono text-slate-800">{frame.ocr_text}</span>
                        </div>
                      )}
                      {frame.logo_manufacturer && (
                        <div>
                          <span className="text-slate-500">Logo:</span>{" "}
                          <span className="font-medium text-slate-800">
                            {frame.logo_manufacturer}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
