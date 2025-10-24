"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export default function CameraSetupPage() {
  const router = useRouter();
  const [cameraUrl, setCameraUrl] = useState<string>("");
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string>("");

  const presets = [
    {
      name: "IP Webcam (HTTP MJPEG)",
      icon: "📱",
      placeholder: "http://192.168.1.100:8080/video",
      description: "For IP Webcam app on Android/iOS",
    },
    {
      name: "IP Webcam (RTSP)",
      icon: "📱",
      placeholder: "rtsp://192.168.1.100:8080/h264",
      description: "RTSP stream from IP Webcam app",
    },
    {
      name: "USB Webcam #0",
      icon: "📹",
      placeholder: "0",
      description: "Primary USB camera connected to server",
    },
    {
      name: "USB Webcam #1",
      icon: "📹",
      placeholder: "1",
      description: "Secondary USB camera",
    },
  ];

  const handlePresetClick = (placeholder: string) => {
    setCameraUrl(placeholder);
    setError("");
  };

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    
    if (!cameraUrl) {
      setError("Please enter a camera URL or select a preset");
      return;
    }
    
    setStarting(true);
    setError("");
    
    try {
      const res = await fetch("http://localhost:8002/camera/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ camera_url: cameraUrl }),
      });
      
      const data = await res.json();
      
      if (res.ok && data.status === "started") {
        // Camera started successfully, navigate to live page
        router.push("/live");
      } else {
        setError(data.detail || data.error || "Failed to start camera");
      }
    } catch (err: any) {
      setError(`Connection error: ${err.message}. Make sure backend is running.`);
    } finally {
      setStarting(false);
    }
  }

  return (
    <section className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-800 mb-2">Camera Setup</h1>
        <p className="text-slate-600">Connect to an IP camera or USB webcam for live inspection</p>
      </div>

      <form onSubmit={onSubmit} className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
        {/* Camera URL Input */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Camera URL or Device ID
          </label>
          <input
            type="text"
            value={cameraUrl}
            onChange={(e) => {
              setCameraUrl(e.target.value);
              setError("");
            }}
            placeholder="http://192.168.1.100:8080/video or rtsp://... or 0"
            className="block w-full px-4 py-3 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-700 font-mono text-sm"
            required
          />
          <p className="mt-2 text-xs text-slate-500">
            Enter HTTP MJPEG URL, RTSP stream URL, or USB device ID (0, 1, 2...)
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-lg p-4">
            <p className="text-rose-700 text-sm font-medium">{error}</p>
          </div>
        )}

        {/* Submit Buttons */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={starting || !cameraUrl}
            className="flex-1 bg-blue-600 text-white py-2.5 px-4 rounded-lg font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors shadow-sm"
          >
            {starting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Starting Camera...
              </span>
            ) : (
              "Start Camera & Go Live"
            )}
          </button>
          <button
            type="button"
            onClick={() => router.push("/live")}
            className="px-4 py-2.5 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 font-medium transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>

      {/* Presets */}
      <div>
        <h2 className="text-lg font-semibold text-slate-800 mb-3">Quick Presets</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {presets.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePresetClick(preset.placeholder)}
              className="bg-white border border-slate-200 rounded-xl p-4 text-left hover:border-blue-400 hover:shadow-md transition-all group"
            >
              <div className="flex items-start gap-3">
                <span className="text-3xl">{preset.icon}</span>
                <div className="flex-1">
                  <h3 className="font-semibold text-slate-800 group-hover:text-blue-600 transition-colors mb-1">
                    {preset.name}
                  </h3>
                  <p className="text-xs text-slate-500 mb-2">{preset.description}</p>
                  <code className="text-xs bg-slate-50 px-2 py-1 rounded text-slate-600 font-mono">
                    {preset.placeholder}
                  </code>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
        <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
          <span className="text-xl">💡</span>
          Setup Instructions
        </h3>
        <div className="space-y-4 text-sm text-blue-800">
          <div>
            <h4 className="font-semibold mb-1">For Android Phone (IP Webcam):</h4>
            <ol className="list-decimal list-inside space-y-1 ml-2">
              <li>Install "IP Webcam" app from Google Play Store</li>
              <li>Open app and scroll to bottom, tap "Start server"</li>
              <li>Note the URL shown (e.g., http://192.168.1.100:8080)</li>
              <li>Add "/video" to the end: http://192.168.1.100:8080/video</li>
              <li>Paste URL above and click "Start Camera"</li>
            </ol>
          </div>
          <div>
            <h4 className="font-semibold mb-1">For USB Webcam:</h4>
            <ol className="list-decimal list-inside space-y-1 ml-2">
              <li>Connect webcam to the server running the backend</li>
              <li>Enter "0" for first camera, "1" for second, etc.</li>
              <li>Click "Start Camera"</li>
            </ol>
          </div>
          <div className="bg-blue-100 rounded-lg p-3 mt-3">
            <p className="font-medium">⚠️ Important:</p>
            <ul className="list-disc list-inside space-y-1 ml-2 mt-1">
              <li>Phone and computer must be on the same WiFi network</li>
              <li>Backend services must be running (docker-compose up)</li>
              <li>Use your phone's actual IP address (check in app)</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
