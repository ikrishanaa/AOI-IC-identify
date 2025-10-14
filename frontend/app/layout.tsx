export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main style={{ padding: 24 }}>
          <header>
            <h1>AOI IC Identify</h1>
            <p>Foundations scaffold - Next.js App Router</p>
          </header>
          {children}
        </main>
      </body>
    </html>
  );
}
