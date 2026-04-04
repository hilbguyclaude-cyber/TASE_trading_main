'use client'

import { useState } from 'react'
import type { Announcement } from '../lib/supabase'

interface AnnouncementRowProps {
  announcement: Announcement
  index: number
  formatDateTime: (isoString: string) => string
}

export function AnnouncementRow({ announcement, index, formatDateTime }: AnnouncementRowProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const truncateContent = (text: string, maxLength: number = 100) => {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength)
  }

  const shouldShowExpandButton = announcement.content.length > 100

  return (
    <tr className="hover:bg-gray-50 transition-colors duration-150">
      {/* 1. Serial Number - Sticky */}
      <td className="sticky-col sticky-col-1 px-3 py-4 whitespace-nowrap text-sm text-gray-900 text-right border-r border-gray-200">
        {index + 1}
      </td>

      {/* 2. Company Name (Hebrew) - Sticky */}
      <td className="sticky-col sticky-col-2 px-3 py-4 text-sm text-gray-900 text-right whitespace-nowrap border-r border-gray-200 font-medium">
        {announcement.company_name}
      </td>

      {/* 3. Title - Sticky */}
      <td className="sticky-col sticky-col-3 px-3 py-4 text-sm text-gray-900 text-right border-r-2 border-gray-300">
        {announcement.title}
      </td>

      {/* 4. Timestamp */}
      <td className="px-3 py-4 text-sm text-gray-500 text-right whitespace-nowrap">
        {formatDateTime(announcement.published_at)}
      </td>

      {/* 5. Content with Expand/Collapse */}
      <td className="px-3 py-4 text-sm text-gray-700 text-right" style={{ maxWidth: '300px' }}>
        <div className={isExpanded ? 'content-expanded' : 'content-collapsed'}>
          {isExpanded ? announcement.content : truncateContent(announcement.content)}
        </div>
        {shouldShowExpandButton && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="expand-button mt-1 text-right block w-full"
          >
            {isExpanded ? 'הסתר' : '...קרא עוד'}
          </button>
        )}
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
                className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs hover:bg-blue-100 transition-colors duration-150 badge-info"
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
          <span className={`badge ${
            announcement.sentiment === 'POSITIVE' ? 'badge-success' :
            announcement.sentiment === 'NEGATIVE' ? 'badge-danger' :
            'badge-info'
          }`}>
            {announcement.sentiment}
          </span>
        ) : (
          <span className="badge badge-warning">PENDING</span>
        )}
      </td>

      {/* 8-16. Stock Prices (t0-t90) - Placeholders */}
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
      <td className="px-3 py-4 text-sm text-gray-900 text-right whitespace-nowrap">
        {announcement.ticker}
      </td>

      {/* 18. Company Name (English) - Placeholder */}
      <td className="px-3 py-4 text-sm text-gray-400 text-left whitespace-nowrap">-</td>

      {/* 19. Ticker (English) - Placeholder */}
      <td className="px-3 py-4 text-sm text-gray-400 text-left whitespace-nowrap">-</td>
    </tr>
  )
}
