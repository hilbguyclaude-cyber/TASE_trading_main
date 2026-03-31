import { supabase, type Announcement, type Position, type SystemStatus } from './lib/supabase'

// Server Component - fetches data on the server
export const revalidate = 60 // Revalidate every 60 seconds

interface DashboardData {
  systemStatus: SystemStatus | null
  recentAnnouncements: Announcement[]
  recentPositions: Position[]
  stats: {
    totalPositions: number
    openPositions: number
    closedPositions: number
    totalProfitLoss: number
    winRate: number
    avgHoldTime: number
  }
}

async function getDashboardData(): Promise<DashboardData> {
  try {
    // Fetch system status
    const { data: systemStatus } = await supabase
      .from('system_status')
      .select('*')
      .single()

    // Fetch recent announcements (last 10)
    const { data: recentAnnouncements } = await supabase
      .from('announcements')
      .select('*')
      .order('published_at', { ascending: false })
      .limit(10)

    // Fetch recent positions (last 10 closed + all open)
    const { data: recentPositions } = await supabase
      .from('positions')
      .select('*')
      .order('entry_time', { ascending: false })
      .limit(20)

    // Calculate statistics
    const { data: allPositions } = await supabase
      .from('positions')
      .select('*')

    const positions = allPositions || []
    const closedPositions = positions.filter(p => p.exit_time !== null)
    const openPositions = positions.filter(p => p.exit_time === null)

    const totalProfitLoss = closedPositions.reduce((sum, p) => sum + (p.profit_loss_ils || 0), 0)
    const winningTrades = closedPositions.filter(p => (p.profit_loss_ils || 0) > 0).length
    const winRate = closedPositions.length > 0 ? (winningTrades / closedPositions.length) * 100 : 0

    // Calculate average hold time (in minutes)
    const holdTimes = closedPositions.map(p => {
      const entry = new Date(p.entry_time).getTime()
      const exit = new Date(p.exit_time!).getTime()
      return (exit - entry) / (1000 * 60) // Convert to minutes
    })
    const avgHoldTime = holdTimes.length > 0
      ? holdTimes.reduce((sum, time) => sum + time, 0) / holdTimes.length
      : 0

    return {
      systemStatus: systemStatus || null,
      recentAnnouncements: recentAnnouncements || [],
      recentPositions: recentPositions || [],
      stats: {
        totalPositions: positions.length,
        openPositions: openPositions.length,
        closedPositions: closedPositions.length,
        totalProfitLoss,
        winRate,
        avgHoldTime
      }
    }
  } catch (error) {
    console.error('Error fetching dashboard data:', error)
    return {
      systemStatus: null,
      recentAnnouncements: [],
      recentPositions: [],
      stats: {
        totalPositions: 0,
        openPositions: 0,
        closedPositions: 0,
        totalProfitLoss: 0,
        winRate: 0,
        avgHoldTime: 0
      }
    }
  }
}

function formatCurrency(value: number): string {
  return `₪${value.toFixed(2)}`
}

function formatPercent(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString('he-IL', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export default async function Dashboard() {
  const data = await getDashboardData()

  return (
    <div className="animate-slide-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold gradient-text mb-2">TASE Trading Dashboard</h1>
        <p className="text-gray-600">Real-time sentiment-based algorithmic trading system</p>
      </div>

      {/* System Status Banner */}
      <div className="card-elevated mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              {data.systemStatus?.status === 'HEALTHY' && (
                <span className="status-dot-success"></span>
              )}
              {data.systemStatus?.status === 'DEGRADED' && (
                <span className="status-dot-warning"></span>
              )}
              {data.systemStatus?.status === 'DOWN' && (
                <span className="status-dot-danger"></span>
              )}
              <span className="text-lg font-semibold text-gray-900">
                System {data.systemStatus?.status || 'Unknown'}
              </span>
            </div>
            <div className="h-8 w-px bg-gray-300"></div>
            <div className="flex items-center space-x-6">
              <div className="flex items-center">
                <span className="text-sm text-gray-600 mr-2">Buying:</span>
                <span className={`badge ${data.systemStatus?.buying_enabled ? 'badge-success' : 'badge-danger'}`}>
                  {data.systemStatus?.buying_enabled ? 'ON' : 'OFF'}
                </span>
              </div>
              <div className="flex items-center">
                <span className="text-sm text-gray-600 mr-2">Selling:</span>
                <span className={`badge ${data.systemStatus?.selling_enabled ? 'badge-success' : 'badge-danger'}`}>
                  {data.systemStatus?.selling_enabled ? 'ON' : 'OFF'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="stat-card group">
          <div className="flex justify-between items-start mb-4">
            <div className="text-sm font-medium text-gray-500 uppercase tracking-wide">Total Positions</div>
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center group-hover:bg-blue-200 transition-colors">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
          <div className="text-4xl font-bold text-gray-900 mb-2">{data.stats.totalPositions}</div>
          <div className="text-sm text-gray-600">
            <span className="text-green-600 font-medium">{data.stats.openPositions} open</span> •
            <span className="ml-1">{data.stats.closedPositions} closed</span>
          </div>
        </div>

        <div className="stat-card group">
          <div className="flex justify-between items-start mb-4">
            <div className="text-sm font-medium text-gray-500 uppercase tracking-wide">Total P/L</div>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center group-hover:opacity-90 transition-colors ${
              data.stats.totalProfitLoss >= 0 ? 'bg-green-100' : 'bg-red-100'
            }`}>
              <svg className={`w-5 h-5 ${data.stats.totalProfitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className={`text-4xl font-bold mb-2 ${data.stats.totalProfitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(data.stats.totalProfitLoss)}
          </div>
          <div className="text-sm text-gray-600">From {data.stats.closedPositions} closed trades</div>
        </div>

        <div className="stat-card group">
          <div className="flex justify-between items-start mb-4">
            <div className="text-sm font-medium text-gray-500 uppercase tracking-wide">Win Rate</div>
            <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center group-hover:bg-purple-200 transition-colors">
              <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="text-4xl font-bold text-gray-900 mb-2">{data.stats.winRate.toFixed(1)}%</div>
          <div className="text-sm text-gray-600">Success rate of closed positions</div>
        </div>

        <div className="stat-card group">
          <div className="flex justify-between items-start mb-4">
            <div className="text-sm font-medium text-gray-500 uppercase tracking-wide">Avg Hold Time</div>
            <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center group-hover:bg-orange-200 transition-colors">
              <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="text-4xl font-bold text-gray-900 mb-2">{data.stats.avgHoldTime.toFixed(0)}</div>
          <div className="text-sm text-gray-600">Minutes per position</div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Recent Announcements */}
        <div className="card hover-lift">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Recent Announcements</h2>
            <a href="/announcements" className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center">
              View all
              <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </a>
          </div>
          {data.recentAnnouncements.length > 0 ? (
            <div className="space-y-4">
              {data.recentAnnouncements.slice(0, 5).map((announcement, idx) => (
                <div key={announcement.id} className="pb-4 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 -mx-6 px-6 rounded-lg transition-colors">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="font-semibold text-gray-900">{announcement.company_name}</span>
                        {announcement.sentiment && (
                          <span className={`badge ${
                            announcement.sentiment === 'POSITIVE' ? 'badge-success' :
                            announcement.sentiment === 'NEGATIVE' ? 'badge-danger' :
                            'badge-info'
                          }`}>
                            {announcement.sentiment}
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600 mb-1 line-clamp-2">{announcement.title}</div>
                      <div className="text-xs text-gray-500">
                        {formatDateTime(announcement.published_at)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-gray-500 font-medium">No announcements yet</p>
              <p className="text-gray-400 text-sm mt-1">Announcements will appear here automatically</p>
            </div>
          )}
        </div>

        {/* Recent Positions */}
        <div className="card hover-lift">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Recent Positions</h2>
            <a href="/positions" className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center">
              View all
              <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </a>
          </div>
          {data.recentPositions.length > 0 ? (
            <div className="space-y-4">
              {data.recentPositions.slice(0, 5).map((position, idx) => (
                <div key={position.id} className="pb-4 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 -mx-6 px-6 rounded-lg transition-colors">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="font-bold text-lg text-gray-900">{position.ticker}</span>
                        {!position.exit_price && (
                          <span className="badge badge-info">OPEN</span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600 mb-1">
                        {formatCurrency(position.entry_price)}
                        <svg className="w-3 h-3 inline mx-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                        {position.exit_price ? formatCurrency(position.exit_price) : 'Monitoring'}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatDateTime(position.entry_time)}
                      </div>
                    </div>
                    <div className="text-right">
                      {position.exit_price && (
                        <div className={`text-2xl font-bold ${
                          (position.profit_loss_percent || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatPercent(position.profit_loss_percent || 0)}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              <p className="text-gray-500 font-medium">No positions yet</p>
              <p className="text-gray-400 text-sm mt-1">Positions will appear when trades are executed</p>
            </div>
          )}
        </div>
      </div>

      {/* Sentiment Correlation Info */}
      <div className="card-elevated">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 mb-3">AI-Powered Sentiment Trading</h2>
            <p className="text-gray-600 mb-6">
              This system uses advanced AI to analyze TASE announcements in real-time, determining sentiment and confidence levels to make automated trading decisions.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-green-50 to-green-100 p-5 rounded-xl border border-green-200">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-green-900 font-bold">POSITIVE</span>
                </div>
                <p className="text-sm text-green-800">
                  Triggers BUY when confidence ≥ 70%
                </p>
              </div>
              <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-5 rounded-xl border border-gray-200">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-8 h-8 rounded-full bg-gray-500 flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                    </svg>
                  </div>
                  <span className="text-gray-900 font-bold">NEUTRAL</span>
                </div>
                <p className="text-sm text-gray-800">
                  No action - position not created
                </p>
              </div>
              <div className="bg-gradient-to-br from-red-50 to-red-100 p-5 rounded-xl border border-red-200">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </div>
                  <span className="text-red-900 font-bold">NEGATIVE</span>
                </div>
                <p className="text-sm text-red-800">
                  No action - position not created
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
