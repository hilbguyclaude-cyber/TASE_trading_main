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
            <input
              type="text"
              placeholder="🔍 Search ticker, company, title, content..."
              style={{ width: '100%', padding: '10px 16px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '14px' }}
            />
          </div>
          <select style={{ padding: '10px 16px', border: '1px solid #d1d5db', borderRadius: '8px', background: 'white', fontSize: '14px', cursor: 'pointer' }}>
            <option>All Sentiments</option>
            <option>Positive</option>
            <option>Negative</option>
            <option>Neutral</option>
            <option>Pending</option>
          </select>
          <select style={{ padding: '10px 16px', border: '1px solid #d1d5db', borderRadius: '8px', background: 'white', fontSize: '14px', cursor: 'pointer' }}>
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
        <div style={{ overflowX: 'auto', scrollBehavior: 'smooth' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ background: '#f9fafb' }}>
              <tr>
                <th style={{ position: 'sticky', left: 0, background: '#f9fafb', zIndex: 10, width: '50px', padding: '12px', textAlign: 'right', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', borderRight: '1px solid #e5e7eb', borderBottom: '2px solid #e5e7eb' }}>#</th>
                <th style={{ position: 'sticky', left: '50px', background: '#f9fafb', zIndex: 10, width: '140px', padding: '12px', textAlign: 'right', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', borderRight: '1px solid #e5e7eb', borderBottom: '2px solid #e5e7eb' }}>שם חברה</th>
                <th style={{ position: 'sticky', left: '190px', background: '#f9fafb', zIndex: 10, width: '220px', padding: '12px', textAlign: 'right', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', borderRight: '2px solid #d1d5db', borderBottom: '2px solid #e5e7eb' }}>כותרת</th>
                <th style={{ padding: '12px', textAlign: 'right', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>תאריך</th>
                <th style={{ padding: '12px', textAlign: 'right', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', minWidth: '300px', borderBottom: '2px solid #e5e7eb' }}>תוכן</th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>קבצים</th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>Sentiment</th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>t0</th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>t1</th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>t5</th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>t10</th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>t15</th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>t30</th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>t45</th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>t60</th>
                <th style={{ padding: '12px', textAlign: 'center', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>t90</th>
                <th style={{ padding: '12px', textAlign: 'right', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>סימול (עב)</th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>Company (EN)</th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', whiteSpace: 'nowrap', borderBottom: '2px solid #e5e7eb' }}>Ticker (EN)</th>
              </tr>
            </thead>
            <tbody style={{ background: 'white' }}>
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
                  <td colSpan={19} style={{ padding: '32px 12px', textAlign: 'center', color: '#6b7280' }}>
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
