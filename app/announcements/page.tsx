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
  const analyzedCount = announcements.filter(a => a.analyzed).length
  const positiveCount = announcements.filter(a => a.sentiment === 'POSITIVE').length
  const negativeCount = announcements.filter(a => a.sentiment === 'NEGATIVE').length
  const neutralCount = announcements.filter(a => a.sentiment === 'NEUTRAL').length

  // Format dates on the server side to avoid passing functions to client components
  const announcementsWithFormattedDates = announcements.map(a => ({
    ...a,
    formattedDate: formatDateTime(a.published_at)
  }))

  return (
    <div className="p-4">
      <h1 className="text-3xl font-bold mb-6">TASE Announcements Dashboard</h1>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5">
          <div className="text-gray-600 text-sm font-medium">Total</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">{announcements.length}</div>
          <div className="text-xs text-gray-500 mt-2">{analyzedCount} analyzed</div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5">
          <div className="text-gray-600 text-sm font-medium">Positive</div>
          <div className="text-3xl font-bold text-green-600 mt-2">{positiveCount}</div>
          <div className="text-xs text-gray-500 mt-2">
            {announcements.length > 0 ? ((positiveCount / announcements.length) * 100).toFixed(0) : 0}%
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5">
          <div className="text-gray-600 text-sm font-medium">Negative</div>
          <div className="text-3xl font-bold text-red-600 mt-2">{negativeCount}</div>
          <div className="text-xs text-gray-500 mt-2">
            {announcements.length > 0 ? ((negativeCount / announcements.length) * 100).toFixed(0) : 0}%
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5">
          <div className="text-gray-600 text-sm font-medium">Neutral</div>
          <div className="text-3xl font-bold text-blue-600 mt-2">{neutralCount}</div>
          <div className="text-xs text-gray-500 mt-2">
            {announcements.length > 0 ? ((neutralCount / announcements.length) * 100).toFixed(0) : 0}%
          </div>
        </div>
      </div>

      {/* Announcements Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
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
