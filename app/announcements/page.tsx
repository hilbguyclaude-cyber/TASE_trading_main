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
    <div>
      <h1 className="text-3xl font-bold mb-6">Announcements</h1>

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

      {/* Announcements Feed */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Recent Announcements</h2>
        {announcements.length > 0 ? (
          <div className="space-y-4">
            {announcements.map((announcement) => (
              <div key={announcement.id} className="border-b pb-4 last:border-b-0">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{announcement.company_name}</span>
                      <span className="text-sm text-gray-500">({announcement.ticker})</span>
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {formatDateTime(announcement.published_at)}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {announcement.analyzed ? (
                      <>
                        <span className={`badge ${
                          announcement.sentiment === 'POSITIVE' ? 'badge-success' :
                          announcement.sentiment === 'NEGATIVE' ? 'badge-danger' :
                          'badge-info'
                        }`}>
                          {announcement.sentiment}
                        </span>
                        {announcement.confidence !== null && (
                          <span className="badge badge-info text-xs">
                            {(announcement.confidence * 100).toFixed(0)}%
                          </span>
                        )}
                      </>
                    ) : (
                      <span className="badge badge-warning text-xs">PENDING</span>
                    )}
                  </div>
                </div>
                <h3 className="font-semibold mb-2">{announcement.title}</h3>
                <p className="text-sm text-gray-700 mb-2 line-clamp-2">{announcement.content}</p>

                {/* Attached Files */}
                {announcement.attached_files && announcement.attached_files.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    {announcement.attached_files.map((file: { name: string; url: string; type: string }, idx: number) => (
                      <a
                        key={idx}
                        href={file.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs hover:bg-blue-100"
                      >
                        📎 {file.type.toUpperCase()}
                      </a>
                    ))}
                  </div>
                )}

                {announcement.reasoning && (
                  <div className="bg-gray-50 p-3 rounded text-sm">
                    <div className="font-semibold text-gray-700 mb-1">AI Analysis:</div>
                    <div className="text-gray-600">{announcement.reasoning}</div>
                  </div>
                )}
                {announcement.source_url && (
                  <a
                    href={announcement.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 text-sm mt-2 inline-block hover:underline"
                  >
                    View source →
                  </a>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No announcements yet</p>
        )}
      </div>
    </div>
  )
}
