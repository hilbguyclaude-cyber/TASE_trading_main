import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TASE Trading Dashboard',
  description: 'Algorithmic trading system for Tel Aviv Stock Exchange',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="bg-blue-600 text-white p-4">
          <div className="container mx-auto flex justify-between items-center">
            <h1 className="text-2xl font-bold">TASE Trading</h1>
            <div className="space-x-4">
              <a href="/" className="hover:underline">Dashboard</a>
              <a href="/positions" className="hover:underline">Positions</a>
              <a href="/announcements" className="hover:underline">Announcements</a>
            </div>
          </div>
        </nav>
        <main className="container mx-auto p-4">
          {children}
        </main>
      </body>
    </html>
  )
}
