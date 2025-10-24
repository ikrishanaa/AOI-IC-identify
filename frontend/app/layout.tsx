import Link from "next/link";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main style={{ padding: 24 }}>
          <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
            <div>
              <h1 style={{ margin: 0 }}>AOI IC Identify</h1>
              <p style={{ margin: 0, color: "#666" }}>Dashboard • Batch • Live</p>
            </div>
            <nav style={{ display: "flex", gap: 12 }}>
              <Link href="/">Dashboard</Link>
              <Link href="/new">New Inspection</Link>
              <Link href="/live">Live</Link>
            </nav>
          </header>
          <div style={{ height: 16 }} />
          {children}
        </main>
      </body>
    </html>
  );
}
