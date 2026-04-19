'use client'

import { useState, useEffect } from 'react'

interface IBKRStatus {
  trading_mode: string
  connected: boolean
  account: string | null
  gateway_host: string
  message: string
}

export default function SystemPage() {
  const [ibkrStatus, setIbkrStatus] = useState<IBKRStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/ibkr_status')
      if (!res.ok) throw new Error('Failed to fetch status')
      const data = await res.json()
      setIbkrStatus(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'LIVE': return 'bg-red-100 text-red-800 border-red-200'
      case 'PAPER': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getStatusColor = (connected: boolean) => {
    return connected
      ? 'bg-green-100 text-green-800'
      : 'bg-red-100 text-red-800'
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">System Status</h1>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">IBKR Connection</h2>
            <button
              onClick={fetchStatus}
              disabled={loading}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Checking...' : 'Refresh'}
            </button>
          </div>

          {error && (
            <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-4">
              Error: {error}
            </div>
          )}

          {ibkrStatus && (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <span className="text-gray-600 w-32">Trading Mode:</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getModeColor(ibkrStatus.trading_mode)}`}>
                  {ibkrStatus.trading_mode}
                </span>
              </div>

              <div className="flex items-center gap-4">
                <span className="text-gray-600 w-32">Status:</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(ibkrStatus.connected)}`}>
                  {ibkrStatus.connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {ibkrStatus.account && (
                <div className="flex items-center gap-4">
                  <span className="text-gray-600 w-32">Account:</span>
                  <span className="text-gray-900 font-mono">{ibkrStatus.account}</span>
                </div>
              )}

              <div className="flex items-center gap-4">
                <span className="text-gray-600 w-32">Gateway Host:</span>
                <span className="text-gray-900 font-mono">{ibkrStatus.gateway_host}</span>
              </div>

              {ibkrStatus.message && (
                <div className="flex items-center gap-4">
                  <span className="text-gray-600 w-32">Message:</span>
                  <span className="text-gray-700">{ibkrStatus.message}</span>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="text-sm text-gray-500">
          <p><strong>DRY_RUN:</strong> Simulated orders, no real trades</p>
          <p><strong>PAPER:</strong> Paper trading via IB Gateway (port 4002)</p>
          <p><strong>LIVE:</strong> Real money trading via IB Gateway (port 4001)</p>
        </div>
      </div>
    </div>
  )
}
