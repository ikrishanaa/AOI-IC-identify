"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

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

  const [job, setJob] = useState<{ id: number; status: string } | null>(null);
  const [jobDetails, setJobDetails] = useState<any>(null);
  const [jobLoading, setJobLoading] = useState(false);

  const [wsStatus, setWsStatus] = useState<string>("idle");
  const [wsMessage, setWsMessage] = useState<string>("");
  const wsRef = useRef<WebSocket | null>(null);

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

  const createJob = useCallback(async () => {
    setJobLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/jobs`, { method: "POST" });
      const data = await res.json();
      setJob(data);
      setJobDetails(null);
    } finally {
      setJobLoading(false);
    }
  }, [apiBase]);

  const fetchJob = useCallback(async () => {
    if (!job?.id) return;
    setJobLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/jobs/${job.id}`);
      const data = await res.json();
      setJobDetails(data);
    } finally {
      setJobLoading(false);
    }
  }, [apiBase, job?.id]);

  const testWs = useCallback(() => {
    try {
      if (wsRef.current) {
        wsRef.current.close();
      }
      setWsStatus("connecting");
      const ws = new WebSocket("ws://localhost:8002/ws/live/analysis");
      wsRef.current = ws;
      ws.onopen = () => setWsStatus("open");
      ws.onmessage = (ev) => setWsMessage(String(ev.data));
      ws.onclose = () => setWsStatus("closed");
      ws.onerror = () => setWsStatus("error");
    } catch (e) {
      setWsStatus("error");
    }
  }, []);

  useEffect(() => {
    refreshHealth();
    return () => {
      wsRef.current?.close();
    };
  }, [refreshHealth]);

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <h2>AOI Dashboard</h2>

      <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3>Service health</h3>
          <button onClick={refreshHealth} disabled={loadingHealth}>
            {loadingHealth ? "Refreshing..." : "Refresh"}
          </button>
        </header>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginTop: 12 }}>
          {[
            ["api_gateway", "API Gateway"],
            ["inspection_service", "Inspection"],
            ["stream_ingestion_service", "Stream Ingestion"],
            ["decision_engine", "Decision Engine"],
            ["verification_service", "Verification"],
          ].map(([key, label]) => {
            const val: any = (health as any)?.[key as keyof Health];
            const ok = val && (val.status === "ok" || val.db === "ok");
            return (
              <div key={String(key)} style={{ border: "1px solid #eee", borderRadius: 8, padding: 12 }}>
                <div style={{ fontWeight: 600 }}>{label}</div>
                <div style={{ color: ok ? "#0a0" : "#a00" }}>{ok ? "OK" : "Unknown/Down"}</div>
                <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", fontSize: 12, color: "#555", marginTop: 8 }}>
                  {val ? JSON.stringify(val, null, 2) : "no data"}
                </pre>
              </div>
            );
          })}
        </div>
      </section>

      <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
        <h3>Batch job (Inspection Service)</h3>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button onClick={createJob} disabled={jobLoading}>Create Job</button>
          {job && <span>Created Job ID: <strong>{job.id}</strong></span>}
          <button onClick={fetchJob} disabled={!job || jobLoading}>Refresh Job</button>
        </div>
        {jobDetails && (
          <pre style={{ marginTop: 12, background: "#fafafa", padding: 12, borderRadius: 6 }}>
            {JSON.stringify(jobDetails, null, 2)}
          </pre>
        )}
      </section>

      <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
        <h3>Live analysis (WebSocket)</h3>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button onClick={testWs}>Connect</button>
          <span>Status: {wsStatus}</span>
        </div>
        {wsMessage && (
          <pre style={{ marginTop: 12, background: "#fafafa", padding: 12, borderRadius: 6 }}>
            {wsMessage}
          </pre>
        )}
      </section>
    </section>
  );
}
