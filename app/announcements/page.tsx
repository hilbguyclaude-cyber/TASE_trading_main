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
    <div className="p-8">
      <div className="mb-2">
        <h1 className="text-3xl font-bold text-gray-900">Announcements</h1>
        <p className="text-gray-600 mt-1">TASE breaking announcements with AI sentiment analysis</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 my-8">
        <div className="bg-white rounded-lg shadow-sm border-l-4 border-blue-500 p-6">
          <div className="text-gray-500 text-xs font-semibold uppercase tracking-wide">Total Announcements</div>
          <div className="text-4xl font-bold text-gray-900 mt-3">{announcements.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border-l-4 border-green-500 p-6">
          <div className="text-gray-500 text-xs font-semibold uppercase tracking-wide">Tradeable</div>
          <div className="text-4xl font-bold text-gray-900 mt-3">{tradeableCount}</div>
          <div className="text-sm text-gray-500 mt-2">
            {announcements.length > 0 ? ((tradeableCount / announcements.length) * 100).toFixed(1) : '0.0'}% of total
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border-l-4 border-purple-500 p-6">
          <div className="text-gray-500 text-xs font-semibold uppercase tracking-wide">Processed</div>
          <div className="text-4xl font-bold text-gray-900 mt-3">{processedCount}</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border-l-4 border-orange-500 p-6">
          <div className="text-gray-500 text-xs font-semibold uppercase tracking-wide">Pending</div>
          <div className="text-4xl font-bold text-gray-900 mt-3">{pendingCount}</div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search ticker, company, title, content..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <select className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white">
            <option>All Sentiments</option>
            <option>Positive</option>
            <option>Negative</option>
            <option>Neutral</option>
            <option>Pending</option>
          </select>
          <select className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white">
            <option>All Announcements</option>
            <option>Analyzed Only</option>
            <option>Pending Only</option>
          </select>
        </div>
        <div className="mt-4 text-sm text-gray-600">
          Showing {announcements.length} of {announcements.length} announcements
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
