import Link from "next/link";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-50 min-h-screen">
        <header className="bg-white border-b border-slate-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-slate-800">AOI IC Identify</h1>
                <p className="text-sm text-slate-500">Automated Optical Inspection System</p>
              </div>
              <nav className="flex gap-2">
                <Link 
                  href="/" 
                  className="px-4 py-2 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors font-medium"
                >
                  Dashboard
                </Link>
                <Link 
                  href="/new" 
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors font-medium"
                >
                  New Inspection
                </Link>
                <Link 
                  href="/live" 
                  className="px-4 py-2 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors font-medium"
                >
                  Live Camera
                </Link>
                <Link 
                  href="/history" 
                  className="px-4 py-2 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors font-medium"
                >
                  History
                </Link>
              </nav>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-6 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
