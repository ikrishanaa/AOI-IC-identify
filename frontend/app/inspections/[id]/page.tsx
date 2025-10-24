"use client";

import { useEffect, useState } from "react";

export default function InspectionDetails({ params }: { params: { id: string } }) {
  const { id } = params;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let timer: any;
    async function tick() {
      try {
        const r = await fetch(`/api/jobs/${id}`, { cache: "no-store" });
        const body = await r.json();
        setData(body);
      } finally {
        setLoading(false);
      }
    }
    tick();
    timer = setInterval(tick, 3000);
    return () => clearInterval(timer);
  }, [id]);

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <h2>Inspection #{id}</h2>
      {loading && <div>Loading...</div>}
      {data && (
        <pre style={{ background: "#fafafa", padding: 12, borderRadius: 8 }}>
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </section>
  );
}
