"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import VerdictBadge from "@/components/VerdictBadge";

type HistoryItem = {
  type: "batch" | "live";
  id: number;
  status: string;
  created_at?: string;
  completed_at?: string;
  started_at?: string;
  ended_at?: string;
  component_type?: string;
  camera_source?: string;
  frames_analyzed?: number;
  pass_count?: number;
  fail_count?: number;
};

export default function HistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "batch" | "live">("all");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchHistory();
  }, [filter]);

  const fetchHistory = async () => {
    setLoading(true);
    setError("");
    try {
      const url = new URL("http://localhost:8001/history");
      if (filter !== "all") {
        url.searchParams.append("inspection_type", filter);
      }
      
      const res = await fetch(url.toString());
      const data = await res.json();
      setHistory(data.history || []);
    } catch (err: any) {
      setError(`Failed to load history: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "N/A";
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-emerald-600 bg-emerald-50";
      case "active":
        return "text-blue-600 bg-blue-50";
      case "failed":
        return "text-rose-600 bg-rose-50";
      case "pending":
        return "text-amber-600 bg-amber-50";
      default:
        return "text-slate-600 bg-slate-50";
    }
  };

  const viewDetails = (item: HistoryItem) => {
    if (item.type === "batch") {
      router.push(`/batch/results/${item.id}`);
    } else {
      router.push(`/history/live/${item.id}`);
    }
  };

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Inspection History</h1>
          <p className="text-slate-600 mt-1">View past batch and live inspections</p>
        </div>
        <button
          onClick={fetchHistory}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
        >
          ⟳ Refresh
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="bg-white border border-slate-200 rounded-xl p-1 flex gap-1">
        {(["all", "batch", "live"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === f
                ? "bg-blue-600 text-white"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            {f === "all" ? "All Inspections" : f === "batch" ? "Batch" : "Live"}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4">
          <p className="text-rose-700 font-medium">{error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center">
          <div className="text-4xl mb-3">⏳</div>
          <p className="text-slate-600">Loading history...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && history.length === 0 && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-12 text-center">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-xl font-semibold text-slate-800 mb-2">No Inspections Yet</h3>
          <p className="text-slate-600 mb-4">
            Start a batch inspection or live analysis to see results here
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => router.push("/batch")}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Batch Inspection
            </button>
            <button
              onClick={() => router.push("/live/setup")}
              className="px-6 py-3 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 transition-colors"
            >
              Live Analysis
            </button>
          </div>
        </div>
      )}

      {/* History List */}
      {!loading && history.length > 0 && (
        <div className="space-y-3">
          {history.map((item) => (
            <div
              key={`${item.type}-${item.id}`}
              className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => viewDetails(item)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold uppercase ${
                        item.type === "batch"
                          ? "bg-purple-100 text-purple-700"
                          : "bg-teal-100 text-teal-700"
                      }`}
                    >
                      {item.type}
                    </span>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(
                        item.status
                      )}`}
                    >
                      {item.status}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">
                      ID: {item.id}
                    </span>
                  </div>

                  <div className="grid md:grid-cols-2 gap-x-6 gap-y-2 mt-3">
                    {item.type === "batch" ? (
                      <>
                        <div className="text-sm">
                          <span className="text-slate-500">Started:</span>{" "}
                          <span className="text-slate-800 font-medium">
                            {formatDate(item.created_at)}
                          </span>
                        </div>
                        {item.completed_at && (
                          <div className="text-sm">
                            <span className="text-slate-500">Completed:</span>{" "}
                            <span className="text-slate-800 font-medium">
                              {formatDate(item.completed_at)}
                            </span>
                          </div>
                        )}
                        {item.component_type && (
                          <div className="text-sm">
                            <span className="text-slate-500">Component:</span>{" "}
                            <span className="text-slate-800 font-medium">
                              {item.component_type}
                            </span>
                          </div>
                        )}
                      </>
                    ) : (
                      <>
                        <div className="text-sm">
                          <span className="text-slate-500">Started:</span>{" "}
                          <span className="text-slate-800 font-medium">
                            {formatDate(item.started_at)}
                          </span>
                        </div>
                        {item.ended_at && (
                          <div className="text-sm">
                            <span className="text-slate-500">Ended:</span>{" "}
                            <span className="text-slate-800 font-medium">
                              {formatDate(item.ended_at)}
                            </span>
                          </div>
                        )}
                        {item.camera_source && (
                          <div className="text-sm md:col-span-2">
                            <span className="text-slate-500">Camera:</span>{" "}
                            <span className="text-slate-800 font-mono text-xs">
                              {item.camera_source}
                            </span>
                          </div>
                        )}
                        {item.frames_analyzed !== undefined && (
                          <div className="text-sm">
                            <span className="text-slate-500">Frames Analyzed:</span>{" "}
                            <span className="text-slate-800 font-semibold">
                              {item.frames_analyzed}
                            </span>
                          </div>
                        )}
                        {(item.pass_count !== undefined ||
                          item.fail_count !== undefined) && (
                          <div className="text-sm">
                            <span className="text-emerald-600 font-semibold">
                              ✓ {item.pass_count || 0}
                            </span>
                            {" / "}
                            <span className="text-rose-600 font-semibold">
                              ✗ {item.fail_count || 0}
                            </span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    viewDetails(item);
                  }}
                  className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-colors"
                >
                  View Details →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
