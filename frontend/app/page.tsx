"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";

type Health = {
  api_gateway?: any;
  inspection_service?: any;
  stream_ingestion_service?: any;
  decision_engine?: any;
  verification_service?: any;
};

export default function Page() {
  const [health, setHealth] = useState<Health | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);

  const apiBase = useMemo(() => (typeof window !== "undefined" ? "" : ""), []);

  const refreshHealth = useCallback(async () => {
    setLoadingHealth(true);
    try {
      const res = await fetch(`${apiBase}/api/services/health`, { cache: "no-store" });
      setHealth(await res.json());
    } catch (e) {
      setHealth({});
    } finally {
      setLoadingHealth(false);
    }
  }, [apiBase]);

  useEffect(() => {
    refreshHealth();
    const interval = setInterval(refreshHealth, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [refreshHealth]);

  return (
    <section className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-8 text-white shadow-lg">
        <h1 className="text-3xl font-bold mb-2">AOI Dashboard</h1>
        <p className="text-blue-100">Automated Optical Inspection System - Monitor and control your inspection workflows</p>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-4">
        <Link href="/new" className="bg-white border border-slate-200 rounded-xl p-6 hover:border-blue-400 hover:shadow-md transition-all group">
          <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">📋</div>
          <h3 className="font-semibold text-slate-800 mb-1 group-hover:text-blue-600 transition-colors">New Inspection</h3>
          <p className="text-sm text-slate-600">Upload and analyze component images</p>
        </Link>
        <Link href="/live" className="bg-white border border-slate-200 rounded-xl p-6 hover:border-blue-400 hover:shadow-md transition-all group">
          <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">📹</div>
          <h3 className="font-semibold text-slate-800 mb-1 group-hover:text-blue-600 transition-colors">Live Camera</h3>
          <p className="text-sm text-slate-600">Real-time component inspection</p>
        </Link>
        <div className="bg-white border border-slate-200 rounded-xl p-6">
          <div className="text-4xl mb-3">📊</div>
          <h3 className="font-semibold text-slate-800 mb-1">Statistics</h3>
          <p className="text-sm text-slate-600">Coming soon...</p>
        </div>
      </div>

      {/* Service Health */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-800">Service Health</h2>
          <button
            onClick={refreshHealth}
            disabled={loadingHealth}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-slate-300 transition-colors text-sm"
          >
            {loadingHealth ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Refreshing
              </span>
            ) : "Refresh"}
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {[
            ["api_gateway", "API Gateway", "🌐"],
            ["inspection_service", "Inspection", "🔍"],
            ["stream_ingestion_service", "Stream", "📹"],
            ["decision_engine", "Decision", "🧠"],
            ["verification_service", "Verification", "✔️"],
          ].map(([key, label, icon]) => {
            const val: any = (health as any)?.[key as keyof Health];
            const ok = val && (val.status === "ok" || val.db === "ok");
            return (
              <div key={String(key)} className="border border-slate-200 rounded-lg p-4 bg-slate-50">
                <div className="text-2xl mb-2">{icon}</div>
                <div className="font-semibold text-slate-800 text-sm mb-1">{label}</div>
                <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${
                  ok 
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200" 
                    : "bg-rose-50 text-rose-700 border border-rose-200"
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${ok ? "bg-emerald-500" : "bg-rose-500"}`}></span>
                  {ok ? "Healthy" : "Down"}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* System Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
        <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
          <span className="text-xl">ℹ️</span>
          System Information
        </h3>
        <div className="grid md:grid-cols-2 gap-4 text-sm text-blue-800">
          <div>
            <p className="font-medium mb-1">Inspection Modes:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Batch: Async processing via Celery queue</li>
              <li>Live: Real-time WebSocket analysis</li>
            </ul>
          </div>
          <div>
            <p className="font-medium mb-1">Verification Signals:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>OCR (30%) - Text extraction</li>
              <li>Logo (25%) - Manufacturer identification</li>
              <li>Visual Signature (25%) - Image comparison</li>
              <li>Anomaly Detection (20%) - Tampering checks</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
