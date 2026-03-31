import { supabase, type Position } from '../lib/supabase'

export const revalidate = 30 // Revalidate every 30 seconds

async function getPositions() {
  try {
    const { data: positions } = await supabase
      .from('positions')
      .select('*')
      .order('entry_time', { ascending: false })

    return positions || []
  } catch (error) {
    console.error('Error fetching positions:', error)
    return []
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

export default async function PositionsPage() {
  const positions = await getPositions()
  const openPositions = positions.filter(p => p.exit_time === null)
  const closedPositions = positions.filter(p => p.exit_time !== null)

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Positions</h1>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card">
          <div className="text-gray-600 text-sm">Total Positions</div>
          <div className="text-3xl font-bold">{positions.length}</div>
        </div>
        <div className="card">
          <div className="text-gray-600 text-sm">Open Positions</div>
          <div className="text-3xl font-bold text-blue-600">{openPositions.length}</div>
        </div>
        <div className="card">
          <div className="text-gray-600 text-sm">Closed Positions</div>
          <div className="text-3xl font-bold text-gray-600">{closedPositions.length}</div>
        </div>
      </div>

      {/* Open Positions */}
      {openPositions.length > 0 && (
        <div className="card mb-6">
          <h2 className="text-xl font-semibold mb-4">Open Positions</h2>
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Company</th>
                  <th>Entry Price</th>
                  <th>Peak Price</th>
                  <th>Position Size</th>
                  <th>Entry Time</th>
                  <th>Sentiment</th>
                </tr>
              </thead>
              <tbody>
                {openPositions.map((position) => (
                  <tr key={position.id}>
                    <td className="font-semibold">{position.ticker}</td>
                    <td>{position.company_name}</td>
                    <td>{formatCurrency(position.entry_price)}</td>
                    <td>{formatCurrency(position.peak_price)}</td>
                    <td>{formatCurrency(position.position_size_ils)}</td>
                    <td className="text-sm">{formatDateTime(position.entry_time)}</td>
                    <td>
                      <span className="badge badge-success text-xs">
                        {position.sentiment} ({(position.confidence * 100).toFixed(0)}%)
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Closed Positions */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Closed Positions</h2>
        {closedPositions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Company</th>
                  <th>Entry → Exit</th>
                  <th>Position Size</th>
                  <th>P/L (₪)</th>
                  <th>P/L (%)</th>
                  <th>Exit Reason</th>
                  <th>Exit Time</th>
                </tr>
              </thead>
              <tbody>
                {closedPositions.map((position) => (
                  <tr key={position.id}>
                    <td className="font-semibold">{position.ticker}</td>
                    <td>{position.company_name}</td>
                    <td className="text-sm">
                      {formatCurrency(position.entry_price)} → {formatCurrency(position.exit_price!)}
                    </td>
                    <td>{formatCurrency(position.position_size_ils)}</td>
                    <td className={`font-semibold ${
                      (position.profit_loss_ils || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(position.profit_loss_ils || 0)}
                    </td>
                    <td className={`font-semibold ${
                      (position.profit_loss_percent || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatPercent(position.profit_loss_percent || 0)}
                    </td>
                    <td className="text-sm text-gray-600">{position.exit_reason}</td>
                    <td className="text-sm">{formatDateTime(position.exit_time!)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500">No closed positions yet</p>
        )}
      </div>
    </div>
  )
}
