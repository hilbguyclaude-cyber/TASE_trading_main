import { supabase, type Announcement } from '../lib/supabase'
import { AnnouncementRow } from './AnnouncementRow'

export const revalidate = 30 // Revalidate every 30 seconds
// Force deployment: 2026-04-04

async function getAnnouncements() {
  try {
    const { data: announcements } = await supabase
      .from('announcements')
      .select('*')
      .order('published_at', { ascending: false })
      .limit(100)

    return announcements || []
  } catch (error) {
    console.error('Error fetching announcements:', error)
    return []
  }
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

export default async function AnnouncementsPage() {
  const announcements = await getAnnouncements()
  const tradeableCount = announcements.filter(a => a.sentiment === 'POSITIVE').length
  const processedCount = announcements.filter(a => a.analyzed && a.sentiment !== 'PENDING').length
  const pendingCount = announcements.filter(a => !a.analyzed || a.sentiment === 'PENDING').length

  // Format dates on the server side to avoid passing functions to client components
  const announcementsWithFormattedDates = announcements.map(a => ({
    ...a,
    formattedDate: formatDateTime(a.published_at)
  }))

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '8px' }}>Announcements</h1>
        <p style={{ color: '#666', fontSize: '14px' }}>TASE breaking announcements with AI sentiment analysis</p>
      </div>

      {/* Summary Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', borderLeft: '4px solid #3b82f6', padding: '24px' }}>
          <div style={{ color: '#6b7280', fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>TOTAL ANNOUNCEMENTS</div>
          <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#111827' }}>{announcements.length}</div>
        </div>
        <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', borderLeft: '4px solid #10b981', padding: '24px' }}>
          <div style={{ color: '#6b7280', fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>TRADEABLE</div>
          <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#111827' }}>{tradeableCount}</div>
          <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '8px' }}>
            {announcements.length > 0 ? ((tradeableCount / announcements.length) * 100).toFixed(1) : '0.0'}% of total
          </div>
        </div>
        <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', borderLeft: '4px solid #8b5cf6', padding: '24px' }}>
          <div style={{ color: '#6b7280', fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>PROCESSED</div>
          <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#111827' }}>{processedCount}</div>
        </div>
        <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', borderLeft: '4px solid #f59e0b', padding: '24px' }}>
          <div style={{ color: '#6b7280', fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>PENDING</div>
          <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#111827' }}>{pendingCount}</div>
        </div>
      </div>

      {/* Search and Filters */}
      <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '16px' }}>
          <div style={{ flex: '1 1 300px' }}>
            <div style={{ position: 'relative' }}>
              <svg style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', width: '20px', height: '20px', color: '#9ca3af' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search ticker, company, title, content..."
                style={{ width: '100%', paddingLeft: '40px', paddingRight: '16px', paddingTop: '10px', paddingBottom: '10px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '14px' }}
              />
            </div>
          </div>
          <select style={{ padding: '10px 16px', border: '1px solid #d1d5db', borderRadius: '8px', background: 'white', fontSize: '14px' }}>
            <option>All Sentiments</option>
            <option>Positive</option>
            <option>Negative</option>
            <option>Neutral</option>
            <option>Pending</option>
          </select>
          <select style={{ padding: '10px 16px', border: '1px solid #d1d5db', borderRadius: '8px', background: 'white', fontSize: '14px' }}>
            <option>All Announcements</option>
            <option>Analyzed Only</option>
            <option>Pending Only</option>
          </select>
        </div>
        <div style={{ fontSize: '14px', color: '#6b7280' }}>
          Showing {announcements.length} of {announcements.length} announcements
        </div>
      </div>

      {/* Announcements Table */}
      <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
        <div className="table-scroll-container">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="sticky-col sticky-col-1 px-3 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider border-r border-gray-200">#</th>
                <th className="sticky-col sticky-col-2 px-3 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider border-r border-gray-200">שם חברה</th>
                <th className="sticky-col sticky-col-3 px-3 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider border-r-2 border-gray-300">כותרת</th>
                <th className="px-3 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">תאריך</th>
                <th className="px-3 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider" style={{ minWidth: '300px' }}>תוכן</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">קבצים</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">Sentiment</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">t0</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">t1</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">t5</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">t10</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">t15</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">t30</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">t45</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">t60</th>
                <th className="px-3 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">t90</th>
                <th className="px-3 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">סימול (עב)</th>
                <th className="px-3 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">Company (EN)</th>
                <th className="px-3 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">Ticker (EN)</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {announcements.length > 0 ? (
                announcementsWithFormattedDates.map((announcement, idx) => (
                  <AnnouncementRow
                    key={announcement.id}
                    announcement={announcement}
                    index={idx}
                  />
                ))
              ) : (
                <tr>
                  <td colSpan={19} className="px-3 py-8 text-center text-gray-500">
                    No announcements yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
