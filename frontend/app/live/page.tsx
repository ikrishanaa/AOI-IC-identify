"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import VerdictBadge from "@/components/VerdictBadge";

type AnalysisResult = {
  verdict: "pass" | "fail" | "needs_review";
  confidence: number;
  score: number;
  ocr?: { text: string; confidence: number };
  logo?: { manufacturer: string; confidence: number };
  visual_signature?: { similarity: number };
  anomaly?: { is_anomalous: boolean; score: number };
  decision_notes?: string[];
};

type CameraStats = {
  running: boolean;
  source?: string;
  frame_count?: number; // captured frames
  frames_analyzed?: number; // analyzed frames
  fps?: number | null;
  sampling_every_n_frames?: number;
  analysis_mode?: "conveyor" | "single";
  error_count?: number;
  last_frame_time?: string;
  analysis_paused?: boolean;
};

export default function LivePage() {
  const router = useRouter();
  const [cameraStats, setCameraStats] = useState<CameraStats | null>(null);
  const [wsStatus, setWsStatus] = useState<"idle" | "connecting" | "open" | "closed" | "error">("idle");
  const [latestResult, setLatestResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string>("");
  const [config, setConfig] = useState<{ analysis_mode: "conveyor" | "single"; store_snapshots: boolean; delete_after: boolean; sampling_every_n_frames: number } | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const statsIntervalRef = useRef<any>(null);

  const feedUrl = useMemo(() => "http://localhost:8002/live/feed", []);

  // Fetch camera stats
  const fetchStats = useCallback(async () => {
    try {
      const [statsRes, cfgRes] = await Promise.all([
        fetch("http://localhost:8002/camera/stats"),
        fetch("http://localhost:8002/analysis/config"),
      ]);
      const stats = await statsRes.json();
      const cfg = await cfgRes.json();
      setCameraStats(stats);
      setConfig(cfg);
      if (!stats.running) {
        setError("Camera not running");
      } else {
        setError("");
      }
    } catch (err) {
      setCameraStats(null);
    }
  }, []);

  // Connect to WebSocket for analysis
  const connectWs = useCallback(() => {
    try {
      wsRef.current?.close();
      setWsStatus("connecting");
      const ws = new WebSocket("ws://localhost:8002/ws/live/analysis");
      wsRef.current = ws;
      
      ws.onopen = () => {
        setWsStatus("open");
        setError("");
      };
      
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === "analysis" && msg.data) {
            setLatestResult(msg.data);
          }
        } catch (err) {
          console.error("Failed to parse WebSocket message", err);
        }
      };
      
      ws.onclose = () => setWsStatus("closed");
      ws.onerror = () => {
        setWsStatus("error");
        setError("WebSocket connection failed");
      };
    } catch {
      setWsStatus("error");
      setError("Failed to connect WebSocket");
    }
  }, []);

  // Update analysis config
  const setMode = useCallback(async (mode: "conveyor" | "single") => {
    try {
      await fetch("http://localhost:8002/analysis/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysis_mode: mode })
      });
      await fetchStats();
    } catch (err: any) {
      setError(`Failed to update mode: ${err.message}`);
    }
  }, [fetchStats]);

  const setSampling = useCallback(async (n: 30 | 60) => {
    try {
      await fetch("http://localhost:8002/analysis/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysis_mode: (config?.analysis_mode || "conveyor"), sampling_every_n_frames: n })
      });
      await fetchStats();
    } catch (err: any) {
      setError(`Failed to set sampling: ${err.message}`);
    }
  }, [config?.analysis_mode, fetchStats]);

  const toggleSnapshots = useCallback(async () => {
    try {
      await fetch("http://localhost:8002/analysis/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysis_mode: (config?.analysis_mode || "conveyor"), store_snapshots: !config?.store_snapshots })
      });
      await fetchStats();
    } catch (err: any) {
      setError(`Failed to toggle snapshots: ${err.message}`);
    }
  }, [config, fetchStats]);

  // Pause analysis
  const pauseAnalysis = useCallback(async () => {
    try {
      await fetch("http://localhost:8002/camera/pause", { method: "POST" });
      await fetchStats();
    } catch (err: any) {
      setError(`Failed to pause: ${err.message}`);
    }
  }, [fetchStats]);

  // Resume analysis
  const resumeAnalysis = useCallback(async () => {
    try {
      await fetch("http://localhost:8002/camera/resume", { method: "POST" });
      await fetchStats();
    } catch (err: any) {
      setError(`Failed to resume: ${err.message}`);
    }
  }, [fetchStats]);

  // Stop camera
  const stopCamera = useCallback(async () => {
    try {
      await fetch("http://localhost:8002/camera/stop", { method: "POST" });
      wsRef.current?.close();
      setCameraStats(null);
      setLatestResult(null);
      setWsStatus("idle");
    } catch (err: any) {
      setError(`Failed to stop camera: ${err.message}`);
    }
  }, []);

  // Poll camera stats
  useEffect(() => {
    fetchStats();
    statsIntervalRef.current = setInterval(fetchStats, 2000);
    return () => {
      if (statsIntervalRef.current) {
        clearInterval(statsIntervalRef.current);
      }
      wsRef.current?.close();
    };
  }, [fetchStats]);

  // Auto-connect WebSocket if camera is running
  useEffect(() => {
    if (cameraStats?.running && wsStatus === "idle") {
      connectWs();
    }
  }, [cameraStats, wsStatus, connectWs]);

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Live Camera Analysis</h1>
          <p className="text-slate-600 mt-1">Real-time component inspection</p>
        </div>
        <div className="flex gap-3 items-center">
          {/* Mode selector */}
          <div className="hidden md:flex items-center gap-1 bg-slate-100 rounded-lg p-1">
            <button
              onClick={() => setMode("conveyor")}
              className={`px-3 py-1.5 rounded-md text-sm font-medium ${config?.analysis_mode === "conveyor" ? "bg-white shadow" : "text-slate-600 hover:bg-slate-200"}`}
            >
              Conveyer-like
            </button>
            <button
              onClick={() => setMode("single")}
              className={`px-3 py-1.5 rounded-md text-sm font-medium ${config?.analysis_mode === "single" ? "bg-white shadow" : "text-slate-600 hover:bg-slate-200"}`}
            >
              1 by 1
            </button>
          </div>

          {cameraStats?.running ? (
            <>
              {cameraStats.analysis_paused ? (
                <button
                  onClick={resumeAnalysis}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 transition-colors"
                >
                  ▶ Resume
                </button>
              ) : (
                <button
                  onClick={pauseAnalysis}
                  className="px-4 py-2 bg-amber-600 text-white rounded-lg font-semibold hover:bg-amber-700 transition-colors"
                >
                  ⏸ Pause
                </button>
              )}
              <button
                onClick={stopCamera}
                className="px-4 py-2 bg-rose-600 text-white rounded-lg font-semibold hover:bg-rose-700 transition-colors"
              >
                ⏹ Stop
              </button>
            </>
          ) : (
            <button
              onClick={() => router.push("/live/setup")}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Setup Camera
            </button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4">
          <p className="text-rose-700 font-medium">{error}</p>
        </div>
      )}

      {/* Camera Not Running State */}
      {!cameraStats?.running && !error && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-8 text-center">
          <div className="text-6xl mb-4">📹</div>
          <h3 className="text-xl font-semibold text-slate-800 mb-2">No Camera Connected</h3>
          <p className="text-slate-600 mb-4">Connect to an IP camera or USB webcam to start live analysis</p>
          <button
            onClick={() => router.push("/live/setup")}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-sm"
          >
            Setup Camera Now
          </button>
        </div>
      )}

      {/* Camera Running - Video Feed & Analysis */}
      {cameraStats?.running && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Video Feed - 2/3 width */}
          <div className="lg:col-span-2">
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-100 border-b border-slate-200 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-lg font-semibold text-slate-800">📹 Live Feed</span>
                  {wsStatus === "open" && (
                    <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600">
                      <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                      LIVE
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-600 font-mono flex items-center gap-3">
                  <span>Captured: {cameraStats.frame_count || 0}</span>
                  <span>Analyzed: {cameraStats.frames_analyzed || 0}</span>
                  {typeof cameraStats.fps === "number" && (
                    <span>FPS: {cameraStats.fps}</span>
                  )}
                </div>
              </div>
              <div className="bg-slate-900 flex items-center justify-center" style={{ minHeight: "400px" }}>
                <img 
                  src={feedUrl} 
                  alt="Live camera feed" 
                  className="max-w-full max-h-[600px] object-contain"
                  onError={() => setError("Failed to load video feed")}
                />
              </div>
            </div>

            {/* Camera Stats */}
            <div className="mt-4 bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <h3 className="font-semibold text-slate-800 mb-3">Camera Status</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                <div>
                  <span className="text-slate-500">Source</span>
                  <p className="font-mono font-medium text-slate-800 truncate">
                    {cameraStats.source || "Unknown"}
                  </p>
                </div>
                <div>
                  <span className="text-slate-500">Mode</span>
                  <p className="font-semibold text-slate-800">{config?.analysis_mode === "single" ? "1 by 1" : "Conveyer-like"}</p>
                </div>
                <div>
                  <span className="text-slate-500">WebSocket</span>
                  <p className={`font-semibold ${
                    wsStatus === "open" ? "text-emerald-600" : 
                    wsStatus === "error" ? "text-rose-600" : "text-slate-600"
                  }`}>
                    {wsStatus.toUpperCase()}
                  </p>
                </div>
                <div>
                  <span className="text-slate-500">Analyzed</span>
                  <p className="font-semibold text-slate-800">{cameraStats.frames_analyzed || 0}</p>
                </div>
                <div>
                  <span className="text-slate-500">Sampling</span>
                  <p className="font-semibold text-slate-800">1 in {cameraStats.sampling_every_n_frames || 30}</p>
                </div>
                <div>
                  <span className="text-slate-500">Errors</span>
                  <p className={`font-semibold ${(cameraStats.error_count || 0) > 0 ? "text-rose-600" : "text-emerald-600"}`}>
                    {cameraStats.error_count || 0}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Analysis Results - 1/3 width */}
          <div className="lg:col-span-1">
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm sticky top-6">
              {/* Conveyor controls */}
              {config?.analysis_mode === "conveyor" && (
                <div className="mb-4 flex items-center justify-between">
                  <div className="text-sm text-slate-700 font-medium">Snapshots</div>
                  <button
                    onClick={toggleSnapshots}
                    className={`px-3 py-1.5 rounded-md text-sm font-medium ${config?.store_snapshots ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-700"}`}
                  >
                    {config?.store_snapshots ? "On" : "Off"}
                  </button>
                </div>
              )}

              {config?.analysis_mode === "conveyor" && (
                <div className="mb-4 flex items-center gap-2">
                  <div className="text-sm text-slate-700 font-medium">Sampling:</div>
                  <button onClick={() => setSampling(30)} className={`px-3 py-1.5 rounded-md text-sm font-medium ${cameraStats?.sampling_every_n_frames === 30 ? "bg-slate-900 text-white" : "bg-slate-200 text-slate-700"}`}>1 in 30</button>
                  <button onClick={() => setSampling(60)} className={`px-3 py-1.5 rounded-md text-sm font-medium ${cameraStats?.sampling_every_n_frames === 60 ? "bg-slate-900 text-white" : "bg-slate-200 text-slate-700"}`}>1 in 60</button>
                </div>
              )}
              <h3 className="font-semibold text-slate-800 mb-4">Latest Analysis</h3>
              
              {!latestResult && (
                <div className="text-center py-8">
                  <div className="text-4xl mb-3">🔍</div>
                  <p className="text-sm text-slate-500">Waiting for analysis...</p>
                </div>
              )}

              {latestResult && (
                <div className="space-y-4">
                  {/* Verdict */}
                  <div>
                    <VerdictBadge 
                      verdict={latestResult.verdict} 
                      confidence={latestResult.confidence}
                      className="text-base"
                    />
                    <div className="mt-2 text-sm text-slate-600">
                      Score: <span className="font-bold text-slate-800">
                        {(latestResult.score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  <div className="border-t border-slate-200 pt-4 space-y-3">
                    {/* OCR */}
                    {latestResult.ocr && (
                      <div className="bg-slate-50 rounded-lg p-3">
                        <div className="text-xs text-slate-500 mb-1">OCR</div>
                        <div className="font-mono font-bold text-sm text-slate-800 mb-1">
                          {latestResult.ocr.text}
                        </div>
                        <div className="text-xs text-slate-600">
                          {(latestResult.ocr.confidence * 100).toFixed(1)}% confidence
                        </div>
                      </div>
                    )}

                    {/* Logo */}
                    {latestResult.logo && (
                      <div className="bg-slate-50 rounded-lg p-3">
                        <div className="text-xs text-slate-500 mb-1">Logo</div>
                        <div className="font-semibold text-sm text-slate-800 mb-1">
                          {latestResult.logo.manufacturer}
                        </div>
                        <div className="text-xs text-slate-600">
                          {(latestResult.logo.confidence * 100).toFixed(1)}% confidence
                        </div>
                      </div>
                    )}

                    {/* Visual Signature */}
                    {latestResult.visual_signature && (
                      <div className="bg-slate-50 rounded-lg p-3">
                        <div className="text-xs text-slate-500 mb-1">Visual Signature</div>
                        <div className="text-sm text-slate-800">
                          {(latestResult.visual_signature.similarity * 100).toFixed(1)}% similarity
                        </div>
                      </div>
                    )}

                    {/* Anomaly */}
                    {latestResult.anomaly && (
                      <div className={`rounded-lg p-3 ${
                        latestResult.anomaly.is_anomalous ? "bg-rose-50" : "bg-emerald-50"
                      }`}>
                        <div className="text-xs text-slate-500 mb-1">Anomaly Detection</div>
                        <div className={`text-sm font-semibold ${
                          latestResult.anomaly.is_anomalous ? "text-rose-700" : "text-emerald-700"
                        }`}>
                          {latestResult.anomaly.is_anomalous ? "⚠ Anomaly Detected" : "✓ Normal"}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Decision Notes */}
                  {latestResult.decision_notes && latestResult.decision_notes.length > 0 && (
                    <div className="border-t border-slate-200 pt-4">
                      <div className="text-xs font-semibold text-slate-700 mb-2">Notes</div>
                      <ul className="text-xs text-slate-600 space-y-1">
                        {latestResult.decision_notes.map((note, idx) => (
                          <li key={idx}>• {note}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
