'use client'

import { Inter } from 'next/font/google'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  // Helper function for link classes
  const linkClass = (isActive: boolean) => {
    return `text-sm font-medium transition-colors duration-200 py-2 ${
      isActive
        ? 'text-gray-900 border-b-2 border-blue-600'
        : 'text-gray-600 hover:text-blue-600'
    }`
  }

  return (
    <html lang="en">
      <body className={inter.className}>
        {/* Navigation Bar - Layout 2 Style */}
        <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
          <div className="container mx-auto px-6">
            <div className="flex items-center justify-between py-4">
              {/* Logo */}
              <div>
                <h1 className="text-xl font-bold text-gray-900">TASE Trading</h1>
              </div>

              {/* Navigation Links */}
              <div className="flex items-center gap-8">
                <Link
                  href="/"
                  className={linkClass(pathname === '/' || pathname === '/announcements')}
                >
                  Home
                </Link>
                <Link
                  href="/dashboard"
                  className={linkClass(pathname === '/dashboard')}
                >
                  Dashboard
                </Link>
                <Link
                  href="/announcements"
                  className={linkClass(pathname === '/announcements')}
                >
                  Announcements
                </Link>
                <Link
                  href="/positions"
                  className={linkClass(pathname === '/positions')}
                >
                  Positions
                </Link>
                <Link
                  href="/intraday"
                  className={linkClass(pathname === '/intraday')}
                >
                  Intraday
                </Link>
                <Link
                  href="/tickers"
                  className={linkClass(pathname === '/tickers')}
                >
                  Tickers
                </Link>
                <Link
                  href="/system"
                  className={linkClass(pathname === '/system')}
                >
                  System
                </Link>
                <Link
                  href="/monitoring"
                  className={linkClass(pathname === '/monitoring')}
                >
                  Monitoring
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="container mx-auto px-6 py-8 max-w-7xl">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-gray-200 mt-16">
          <div className="container mx-auto px-6 py-6">
            <div className="flex justify-between items-center text-sm text-gray-600">
              <p>© 2026 TASE Trading System • Built with Claude Code</p>
              <div className="flex items-center space-x-4">
                <span>Powered by Gemini AI & Supabase</span>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
