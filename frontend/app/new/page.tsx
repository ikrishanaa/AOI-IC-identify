"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export default function NewInspectionPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [fileName, setFileName] = useState<string>("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    try {
      // TODO: wire real upload; for MVP we just create a job
      const r = await fetch("/api/jobs", { method: "POST" });
      const body = await r.json();
      if (r.ok && body?.id) router.push(`/inspections/${body.id}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <h2>New Batch Inspection</h2>
      <form onSubmit={onSubmit} style={{ border: "1px solid #ddd", padding: 16, borderRadius: 8 }}>
        <label style={{ display: "block", marginBottom: 8 }}>Upload image (mocked)</label>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFileName(e.target.files?.[0]?.name || "")}
        />
        {fileName && <div style={{ marginTop: 8, color: "#555" }}>Selected: {fileName}</div>}
        <div style={{ marginTop: 12 }}>
          <button type="submit" disabled={submitting}>
            {submitting ? "Submitting..." : "Submit"}
          </button>
        </div>
      </form>
      <p style={{ color: "#666" }}>Note: Upload is mocked for MVP; backend processes will be integrated next.</p>
    </section>
  );
}
