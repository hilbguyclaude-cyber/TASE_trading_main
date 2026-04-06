'use client'

import { useState } from 'react'
import type { Announcement } from '../lib/supabase'

interface AnnouncementRowProps {
  announcement: Announcement & { formattedDate: string }
  index: number
}

export function AnnouncementRow({ announcement, index }: AnnouncementRowProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const truncateContent = (text: string, maxLength: number = 100) => {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength)
  }

  const shouldShowExpandButton = announcement.content.length > 100

  const getSentimentBadgeStyle = (sentiment: string | null) => {
    const baseStyle = {
      padding: '6px 12px',
      borderRadius: '6px',
      fontSize: '11px',
      fontWeight: 500,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.025em',
      display: 'inline-block'
    }

    if (sentiment === 'positive') {
      return { ...baseStyle, background: '#dcfce7', color: '#16a34a', border: '1px solid #bbf7d0' }
    } else if (sentiment === 'negative') {
      return { ...baseStyle, background: '#fee2e2', color: '#dc2626', border: '1px solid #fecaca' }
    } else if (sentiment === 'PENDING' || sentiment === null) {
      return { ...baseStyle, background: '#fef3c7', color: '#d97706', border: '1px solid #fde68a' }
    } else {
      return { ...baseStyle, background: '#dbeafe', color: '#2563eb', border: '1px solid #bfdbfe' }
    }
  }

  return (
    <tr style={{ transition: 'background-color 0.15s ease' }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f9fafb'} onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}>
      {/* 1. Serial Number - Sticky */}
      <td style={{ position: 'sticky', left: 0, background: 'white', zIndex: 10, minWidth: '80px', padding: '20px 16px', whiteSpace: 'nowrap', fontSize: '14px', color: '#111827', textAlign: 'right', borderRight: '1px solid #e5e7eb', borderBottom: '1px solid #e5e7eb' }}>
        {index + 1}
      </td>

      {/* 2. Company Name (Hebrew) - Sticky */}
      <td style={{ position: 'sticky', left: '80px', background: 'white', zIndex: 10, minWidth: '180px', padding: '20px 16px', fontSize: '14px', color: '#111827', textAlign: 'right', whiteSpace: 'nowrap', borderRight: '2px solid #d1d5db', fontWeight: 500, borderBottom: '1px solid #e5e7eb' }}>
        {announcement.company_name}
      </td>

      {/* 3. Title - Scrollable */}
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#111827', textAlign: 'right', minWidth: '300px', borderBottom: '1px solid #e5e7eb' }}>
        {announcement.title}
      </td>

      {/* 4. Timestamp */}
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#6b7280', textAlign: 'right', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>
        {announcement.formattedDate}
      </td>

      {/* 5. Content with Expand/Collapse */}
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#374151', textAlign: 'right', minWidth: '400px', borderBottom: '1px solid #e5e7eb' }}>
        <div style={isExpanded ? { display: 'block' } : { display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' } as any}>
          {isExpanded ? announcement.content : truncateContent(announcement.content)}
        </div>
        {shouldShowExpandButton && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{ marginTop: '4px', textAlign: 'right', display: 'block', width: '100%', color: '#2563eb', cursor: 'pointer', fontWeight: 500, fontSize: '13px', background: 'none', border: 'none', padding: 0 }}
          >
            {isExpanded ? 'הסתר' : '...קרא עוד'}
          </button>
        )}
      </td>

      {/* 6. Attached Files */}
      <td style={{ padding: '20px 16px', fontSize: '14px', textAlign: 'center', borderBottom: '1px solid #e5e7eb' }}>
        {announcement.attached_files && announcement.attached_files.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {announcement.attached_files.map((file: { name: string; url: string; type: string }, fileIdx: number) => (
              <a
                key={fileIdx}
                href={file.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '4px 8px', borderRadius: '6px', fontSize: '12px', background: '#dbeafe', color: '#2563eb', border: '1px solid #bfdbfe', textDecoration: 'none', transition: 'background-color 0.15s' }}
              >
                📎 {file.type.toUpperCase()}
              </a>
            ))}
          </div>
        ) : (
          <span style={{ color: '#9ca3af' }}>-</span>
        )}
      </td>

      {/* 7. Sentiment */}
      <td style={{ padding: '20px 16px', fontSize: '14px', textAlign: 'center', borderBottom: '1px solid #e5e7eb' }}>
        {announcement.analyzed ? (
          <span style={getSentimentBadgeStyle(announcement.sentiment)}>
            {announcement.sentiment || 'PENDING'}
          </span>
        ) : (
          <span style={getSentimentBadgeStyle('PENDING')}>PENDING</span>
        )}
      </td>

      {/* 8-16. Stock Prices (t0-t90) - Placeholders */}
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#9ca3af', textAlign: 'center', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>-</td>
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#9ca3af', textAlign: 'center', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>-</td>
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#9ca3af', textAlign: 'center', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>-</td>
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#9ca3af', textAlign: 'center', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>-</td>
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#9ca3af', textAlign: 'center', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>-</td>
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#9ca3af', textAlign: 'center', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>-</td>
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#9ca3af', textAlign: 'center', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>-</td>
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#9ca3af', textAlign: 'center', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>-</td>
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#9ca3af', textAlign: 'center', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>-</td>

      {/* 17. Ticker (Hebrew) */}
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#111827', textAlign: 'right', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>
        {announcement.ticker}
      </td>

      {/* 18. Company Name (English) - Placeholder */}
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#9ca3af', textAlign: 'left', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>-</td>

      {/* 19. Ticker (English) - Placeholder */}
      <td style={{ padding: '20px 16px', fontSize: '14px', color: '#9ca3af', textAlign: 'left', whiteSpace: 'nowrap', borderBottom: '1px solid #e5e7eb' }}>-</td>
    </tr>
  )
}
