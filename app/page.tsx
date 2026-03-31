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
    <div>
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>

      {/* System Status */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">System Status</h2>
        {data.systemStatus ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <span className="text-gray-600">Status:</span>
              <span className={`ml-2 badge ${
                data.systemStatus.status === 'HEALTHY' ? 'badge-success' :
                data.systemStatus.status === 'DEGRADED' ? 'badge-warning' :
                'badge-danger'
              }`}>
                {data.systemStatus.status}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Buying:</span>
              <span className={`ml-2 badge ${data.systemStatus.buying_enabled ? 'badge-success' : 'badge-danger'}`}>
                {data.systemStatus.buying_enabled ? 'ENABLED' : 'DISABLED'}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Selling:</span>
              <span className={`ml-2 badge ${data.systemStatus.selling_enabled ? 'badge-success' : 'badge-danger'}`}>
                {data.systemStatus.selling_enabled ? 'ENABLED' : 'DISABLED'}
              </span>
            </div>
          </div>
        ) : (
          <p className="text-gray-500">No system status available</p>
        )}
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <div className="card">
          <div className="text-gray-600 text-sm">Total Positions</div>
          <div className="text-3xl font-bold">{data.stats.totalPositions}</div>
          <div className="text-sm text-gray-500">
            {data.stats.openPositions} open • {data.stats.closedPositions} closed
          </div>
        </div>

        <div className="card">
          <div className="text-gray-600 text-sm">Total P/L</div>
          <div className={`text-3xl font-bold ${data.stats.totalProfitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(data.stats.totalProfitLoss)}
          </div>
          <div className="text-sm text-gray-500">From {data.stats.closedPositions} trades</div>
        </div>

        <div className="card">
          <div className="text-gray-600 text-sm">Win Rate</div>
          <div className="text-3xl font-bold">{data.stats.winRate.toFixed(1)}%</div>
          <div className="text-sm text-gray-500">Of closed positions</div>
        </div>

        <div className="card">
          <div className="text-gray-600 text-sm">Avg Hold Time</div>
          <div className="text-3xl font-bold">{data.stats.avgHoldTime.toFixed(0)}</div>
          <div className="text-sm text-gray-500">Minutes</div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Recent Announcements */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Recent Announcements</h2>
          {data.recentAnnouncements.length > 0 ? (
            <div className="space-y-3">
              {data.recentAnnouncements.slice(0, 5).map((announcement) => (
                <div key={announcement.id} className="border-b pb-3 last:border-b-0">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-semibold text-sm">{announcement.company_name}</div>
                      <div className="text-sm text-gray-600">{announcement.title}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDateTime(announcement.published_at)}
                      </div>
                    </div>
                    {announcement.sentiment && (
                      <span className={`ml-2 badge ${
                        announcement.sentiment === 'POSITIVE' ? 'badge-success' :
                        announcement.sentiment === 'NEGATIVE' ? 'badge-danger' :
                        'badge-info'
                      }`}>
                        {announcement.sentiment}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No announcements yet</p>
          )}
          <a href="/announcements" className="text-blue-600 text-sm mt-4 inline-block hover:underline">
            View all announcements →
          </a>
        </div>

        {/* Recent Positions */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Recent Positions</h2>
          {data.recentPositions.length > 0 ? (
            <div className="space-y-3">
              {data.recentPositions.slice(0, 5).map((position) => (
                <div key={position.id} className="border-b pb-3 last:border-b-0">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-semibold text-sm">{position.ticker}</div>
                      <div className="text-sm text-gray-600">
                        {formatCurrency(position.entry_price)} → {
                          position.exit_price ? formatCurrency(position.exit_price) : 'Open'
                        }
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDateTime(position.entry_time)}
                      </div>
                    </div>
                    <div className="text-right">
                      {position.exit_price ? (
                        <div className={`font-semibold text-sm ${
                          (position.profit_loss_percent || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatPercent(position.profit_loss_percent || 0)}
                        </div>
                      ) : (
                        <span className="badge badge-info text-xs">OPEN</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No positions yet</p>
          )}
          <a href="/positions" className="text-blue-600 text-sm mt-4 inline-block hover:underline">
            View all positions →
          </a>
        </div>
      </div>

      {/* Sentiment Correlation Analysis */}
      <div className="card mt-4">
        <h2 className="text-xl font-semibold mb-4">Sentiment-Price Correlation</h2>
        <p className="text-gray-600">
          This dashboard tracks the correlation between announcement sentiment (analyzed by AI) and
          subsequent price movements. The goal is to validate whether positive sentiment announcements
          lead to profitable trades.
        </p>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-green-50 p-4 rounded">
            <div className="text-green-800 font-semibold">POSITIVE Sentiment</div>
            <div className="text-sm text-green-700 mt-1">
              Triggers BUY positions when confidence ≥ 70%
            </div>
          </div>
          <div className="bg-yellow-50 p-4 rounded">
            <div className="text-yellow-800 font-semibold">NEUTRAL Sentiment</div>
            <div className="text-sm text-yellow-700 mt-1">
              No action taken - position not created
            </div>
          </div>
          <div className="bg-red-50 p-4 rounded">
            <div className="text-red-800 font-semibold">NEGATIVE Sentiment</div>
            <div className="text-sm text-red-700 mt-1">
              No action taken - position not created
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
