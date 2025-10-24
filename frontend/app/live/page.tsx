"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export default function LivePage() {
  const [wsStatus, setWsStatus] = useState("idle");
  const [wsMessage, setWsMessage] = useState("");
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    try {
      wsRef.current?.close();
      setWsStatus("connecting");
      const ws = new WebSocket("ws://localhost:8002/ws/live/analysis");
      wsRef.current = ws;
      ws.onopen = () => setWsStatus("open");
      ws.onmessage = (e) => setWsMessage(String(e.data));
      ws.onclose = () => setWsStatus("closed");
      ws.onerror = () => setWsStatus("error");
    } catch {
      setWsStatus("error");
    }
  }, []);

  useEffect(() => () => wsRef.current?.close(), []);

  // For MVP, video feed endpoint returns 501; keeping placeholder image container
  const feedUrl = useMemo(() => "http://localhost:8002/live/feed", []);

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <h2>Live Analysis</h2>
      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "1fr" }}>
        <div style={{ border: "1px solid #ddd", borderRadius: 8, overflow: "hidden" }}>
          <div style={{ padding: 8, background: "#fafafa", borderBottom: "1px solid #eee" }}>Video Feed</div>
          <div style={{ height: 360, display: "grid", placeItems: "center" }}>
            <img src={feedUrl} alt="Live feed" style={{ maxWidth: "100%" }} />
          </div>
        </div>
        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <button onClick={connect}>Connect</button>
            <span>Status: {wsStatus}</span>
          </div>
          {wsMessage && (
            <pre style={{ marginTop: 8, background: "#fafafa", padding: 12 }}>{wsMessage}</pre>
          )}
        </div>
      </div>
    </section>
  );
}
