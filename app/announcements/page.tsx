import { supabase, type Announcement } from '../lib/supabase'

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

  return (
    <div className="p-4">
      <h1 className="text-3xl font-bold mb-6">TASE Announcements Dashboard</h1>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="card">
          <div className="text-gray-600 text-sm">Total</div>
          <div className="text-3xl font-bold">{announcements.length}</div>
          <div className="text-xs text-gray-500 mt-1">{analyzedCount} analyzed</div>
        </div>
        <div className="card">
          <div className="text-gray-600 text-sm">Positive</div>
          <div className="text-3xl font-bold text-green-600">{positiveCount}</div>
          <div className="text-xs text-gray-500 mt-1">
            {announcements.length > 0 ? ((positiveCount / announcements.length) * 100).toFixed(0) : 0}%
          </div>
        </div>
        <div className="card">
          <div className="text-gray-600 text-sm">Negative</div>
          <div className="text-3xl font-bold text-red-600">{negativeCount}</div>
          <div className="text-xs text-gray-500 mt-1">
            {announcements.length > 0 ? ((negativeCount / announcements.length) * 100).toFixed(0) : 0}%
          </div>
        </div>
        <div className="card">
          <div className="text-gray-600 text-sm">Neutral</div>
          <div className="text-3xl font-bold text-blue-600">{neutralCount}</div>
          <div className="text-xs text-gray-500 mt-1">
            {announcements.length > 0 ? ((neutralCount / announcements.length) * 100).toFixed(0) : 0}%
          </div>
        </div>
      </div>

      {/* Announcements Table */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">#</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">שם חברה</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">תאריך</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[200px]">כותרת</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[300px]">תוכן</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">קבצים</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Sentiment</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">t0</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">t1</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">t5</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">t10</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">t15</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">t30</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">t45</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">t60</th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">t90</th>
              <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">סימול (עב)</th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Company (EN)</th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Ticker (EN)</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {announcements.length > 0 ? (
              announcements.map((announcement, idx) => (
                <tr key={announcement.id} className="hover:bg-gray-50">
                  {/* 1. Serial Number */}
                  <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900 text-right">{idx + 1}</td>

                  {/* 2. Company Name (Hebrew) */}
                  <td className="px-3 py-4 text-sm text-gray-900 text-right whitespace-nowrap">{announcement.company_name}</td>

                  {/* 3. Timestamp */}
                  <td className="px-3 py-4 text-sm text-gray-500 text-right whitespace-nowrap">{formatDateTime(announcement.published_at)}</td>

                  {/* 4. Title */}
                  <td className="px-3 py-4 text-sm text-gray-900 text-right">{announcement.title}</td>

                  {/* 5. Content */}
                  <td className="px-3 py-4 text-sm text-gray-700 text-right max-w-md">
                    <div className="line-clamp-3">{announcement.content}</div>
                  </td>

                  {/* 6. Attached Files */}
                  <td className="px-3 py-4 text-sm text-center">
                    {announcement.attached_files && announcement.attached_files.length > 0 ? (
                      <div className="flex flex-col gap-1">
                        {announcement.attached_files.map((file: { name: string; url: string; type: string }, fileIdx: number) => (
                          <a
                            key={fileIdx}
                            href={file.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs hover:bg-blue-100"
                          >
                            📎 {file.type.toUpperCase()}
                          </a>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>

                  {/* 7. Sentiment */}
                  <td className="px-3 py-4 text-sm text-center">
                    {announcement.analyzed ? (
                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                        announcement.sentiment === 'POSITIVE' ? 'bg-green-100 text-green-800' :
                        announcement.sentiment === 'NEGATIVE' ? 'bg-red-100 text-red-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {announcement.sentiment}
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800">PENDING</span>
                    )}
                  </td>

                  {/* 8-16. Stock Prices (t0, t1, t5, t10, t15, t30, t45, t60, t90) */}
                  <td className="px-3 py-4 text-sm text-gray-400 text-center whitespace-nowrap">-</td>
                  <td className="px-3 py-4 text-sm text-gray-400 text-center whitespace-nowrap">-</td>
                  <td className="px-3 py-4 text-sm text-gray-400 text-center whitespace-nowrap">-</td>
                  <td className="px-3 py-4 text-sm text-gray-400 text-center whitespace-nowrap">-</td>
                  <td className="px-3 py-4 text-sm text-gray-400 text-center whitespace-nowrap">-</td>
                  <td className="px-3 py-4 text-sm text-gray-400 text-center whitespace-nowrap">-</td>
                  <td className="px-3 py-4 text-sm text-gray-400 text-center whitespace-nowrap">-</td>
                  <td className="px-3 py-4 text-sm text-gray-400 text-center whitespace-nowrap">-</td>
                  <td className="px-3 py-4 text-sm text-gray-400 text-center whitespace-nowrap">-</td>

                  {/* 17. Ticker (Hebrew) */}
                  <td className="px-3 py-4 text-sm text-gray-900 text-right whitespace-nowrap">{announcement.ticker}</td>

                  {/* 18. Company Name (English) */}
                  <td className="px-3 py-4 text-sm text-gray-400 text-left whitespace-nowrap">-</td>

                  {/* 19. Ticker (English) */}
                  <td className="px-3 py-4 text-sm text-gray-400 text-left whitespace-nowrap">-</td>
                </tr>
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
  )
}
