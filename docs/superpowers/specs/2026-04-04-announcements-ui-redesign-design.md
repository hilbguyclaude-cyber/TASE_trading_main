# Announcements Dashboard UI Redesign

**Date:** 2026-04-04
**Status:** Approved
**Approach:** Incremental Enhancement

## Overview

Redesign the TASE Trading Dashboard announcements page from a basic 19-column table to a professional, modern interface that supports both historical analysis and real-time monitoring use cases.

## Design Goals

1. **Professional appearance** - Modern Minimal aesthetic with clean design
2. **Comfortable reading** - Prioritize readability over information density
3. **Maintain context** - Fixed left columns keep company/title visible while scrolling
4. **Easy scanning** - Subtle color coding for sentiment and price changes
5. **Incremental approach** - Enhance existing code rather than rebuild

## User Requirements

- **Primary use cases:** Historical comparison (analyze many announcements over time) + Real-time monitoring (watch for new announcements)
- **Information priority:** Comfortable reading experience with good spacing over cramming all data on screen
- **Table needs:** 19 columns with smooth horizontal scrolling

## Visual Design System

### Color Palette (Modern Minimal)

**Base Colors:**
- Background: `#ffffff` (white)
- Page background: `#f8f9fa` (light gray)
- Primary text: `#111827` (dark gray)
- Secondary text: `#6b7280` (medium gray)
- Border: `#e5e7eb` (light gray)
- Shadow: `0 1px 3px rgba(0,0,0,0.1)` (subtle)

**Sentiment Colors (Subtle & Professional):**
- **Positive:**
  - Background: `#dcfce7` (light green)
  - Text: `#16a34a` (dark green)
  - Border: `#bbf7d0` (green)
- **Negative:**
  - Background: `#fee2e2` (light red)
  - Text: `#dc2626` (dark red)
  - Border: `#fecaca` (red)
- **Neutral:**
  - Background: `#dbeafe` (light blue)
  - Text: `#2563eb` (dark blue)
  - Border: `#bfdbfe` (blue)
- **Pending:**
  - Background: `#fef3c7` (light yellow)
  - Text: `#d97706` (dark orange)
  - Border: `#fde68a` (yellow)

**Price Change Colors:**
- Positive changes: Same as sentiment positive colors
- Negative changes: Same as sentiment negative colors
- No change: Gray background `#f8f9fa`, text `#6b7280`

### Typography

- **Column headers:** 12px, font-weight 600, uppercase, letter-spacing 0.5px, color `#6b7280`
- **Table body text:** 14px, font-weight 400
- **Timestamps/metadata:** 12-13px, color `#6b7280`
- **Font family:** Inter (existing from Next.js)

### Spacing

- **Table cell padding:** 12-14px vertical, 12px horizontal
- **Minimum row height:** 48px (auto-height based on content)
- **Column gaps:** 12-16px
- **Card shadows:** Subtle elevation only

## Table Architecture

### Layout Structure

**Two-section layout:**
1. **Fixed Left Section** - Remains visible during horizontal scroll
2. **Scrolling Right Section** - Scrolls horizontally

### Fixed Left Columns (Sticky)

| Column | Width | Content |
|--------|-------|---------|
| # | 50px | Serial number (1, 2, 3...) |
| שם חברה | 140px | Company name (Hebrew) |
| כותרת | 220px | Announcement title (Hebrew) |

**Total fixed width:** ~410px

### Scrolling Right Columns

| Column | Width | Content |
|--------|-------|---------|
| תאריך | 100px | Published timestamp |
| תוכן | 300px | Content with expand/collapse |
| קבצים | 120px | Attached files (PDF badges) |
| Sentiment | 100px | Sentiment badge |
| t0 | 100px | Price at announcement time |
| t1 | 100px | Price 1 min after |
| t5 | 100px | Price 5 min after |
| t10 | 100px | Price 10 min after |
| t15 | 100px | Price 15 min after |
| t30 | 100px | Price 30 min after |
| t45 | 100px | Price 45 min after |
| t60 | 100px | Price 60 min after |
| t90 | 100px | Price 90 min after |
| סימול (עב) | 100px | Ticker (Hebrew) |
| Company (EN) | 140px | Company name (English) |
| Ticker (EN) | 100px | Ticker (English) |

### Technical Implementation

**CSS Grid with Sticky Positioning:**
```css
.table-container {
  display: grid;
  grid-template-columns: 50px 140px 220px [scrollable-start] 100px 300px 120px ... [scrollable-end];
}

.fixed-column {
  position: sticky;
  left: 0; /* or accumulated width for columns 2-3 */
  background: white;
  z-index: 10;
}
```

**Horizontal Scroll:**
- Container has `overflow-x: auto`
- Smooth scrolling behavior
- Scrollbar always visible on desktop

## Interactive Elements

### Content Expand/Collapse

**Default State:**
- Show first 100 characters of announcement content
- Append "...קרא עוד" (Read more) link in blue (`#2563eb`)
- Character counter shows total length

**Expanded State:**
- Show full content text
- Button changes to "הסתר" (Hide)
- Content expands inline with smooth height animation
- Animation: `transition: max-height 0.2s ease-out`

**Implementation:**
- React state per row: `const [expanded, setExpanded] = useState(false)`
- Conditional rendering based on state
- CSS class for animation

### Row Hover States

- Background changes to `#f8f9fa` (very light gray)
- Smooth transition: `transition: background-color 0.15s ease`
- Applies to entire row across both fixed and scrolling sections

### PDF Attachment Badges

**Existing implementation (keep as-is):**
- 📎 icon + file type (e.g., "📎 PDF")
- Background: `#dbeafe` (light blue)
- Text: `#2563eb` (blue)
- Padding: `6px 12px`
- Border-radius: `6px`
- Clickable link, opens in new tab (`target="_blank"`)

### Sentiment Badges

**Badge styling:**
- Padding: `6px 12px`
- Border-radius: `6px`
- Font-size: `11px`
- Font-weight: `500`
- Text-transform: `uppercase`
- Border: `1px solid` (matching color)

**Badge text:**
- POSITIVE
- NEGATIVE
- NEUTRAL
- PENDING

### Price Display Format

**Cell structure:**
```
$24.85
+2.4%
```

**Styling:**
- Price: 14px, font-weight 500, dark gray
- Percentage: 12px, font-weight 500, colored (green/red)
- Stacked vertically with 4px gap
- Background color based on change (light green/red/gray)
- Padding: `8px 12px`
- Border-radius: `6px`

## Summary Stats Section

**Location:** Top of page, above table

**Layout:** 4-card grid (responsive: 1 column mobile, 4 columns desktop)

**Cards:**
1. Total announcements (with analyzed count)
2. Positive sentiment (count + percentage)
3. Negative sentiment (count + percentage)
4. Neutral sentiment (count + percentage)

**Card styling:**
- Background: White
- Border-radius: `12px`
- Box-shadow: `0 1px 3px rgba(0,0,0,0.1)`
- Padding: `24px`
- Hover effect: `translateY(-2px)` with enhanced shadow
- Transition: `all 0.2s ease`

**Color coding:**
- Total: Blue gradient accent
- Positive: Green text
- Negative: Red text
- Neutral: Blue text

## Real-time Updates

**Current implementation (keep):**
- 30-second revalidation via Next.js `revalidate: 30`
- Static generation with ISR (Incremental Static Regeneration)

**Enhancement:**
- Add fade-in animation for newly loaded rows
- Optional: "NEW" badge for announcements < 5 minutes old
  - Badge: Orange background `#fed7aa`, text `#c2410c`
  - Auto-hide after 5 minutes

## Responsive Behavior

**Desktop (>1024px):**
- Full table with horizontal scroll
- All 19 columns visible (via scrolling)
- Fixed left columns at 410px

**Tablet (768px - 1024px):**
- Same as desktop but with adjusted column widths
- Fixed left section may reduce to 2 columns (# and Company)

**Mobile (<768px):**
- Consider alternative card view (future enhancement)
- For now: maintain table with horizontal scroll
- Fixed left section shows only company name

## Data Flow

**No changes to existing data flow:**
- Keep existing Supabase query in `getAnnouncements()`
- Keep existing TypeScript interface `Announcement`
- Keep existing sorting (by `published_at DESC`)
- Keep existing limit (100 announcements)

**Data fields used:**
- `id` - React key
- `company_name` - Fixed left column
- `title` - Fixed left column
- `published_at` - Scrolling column
- `content` - Scrolling column (with expand/collapse)
- `attached_files` - Array of file objects
- `sentiment` - Badge display
- `confidence` - Not displayed (removed from design)
- Price fields (t0-t90) - Placeholder "-" for now

## Testing Strategy

**Visual regression:**
1. Compare before/after screenshots
2. Test all sentiment badge colors
3. Test expand/collapse animation
4. Test horizontal scroll behavior

**Interaction testing:**
1. Verify sticky columns stay fixed during scroll
2. Test expand/collapse on multiple rows simultaneously
3. Test hover states across fixed/scrolling boundary
4. Test PDF link clicks (open new tab)

**Responsive testing:**
1. Test on desktop (1920px, 1440px)
2. Test on tablet (iPad size)
3. Test on mobile (iPhone size)

**Browser testing:**
- Chrome (primary)
- Safari (macOS)
- Firefox (check)

**Accessibility:**
- Keyboard navigation (Tab through interactive elements)
- Screen reader test (announcement row context)
- Color contrast check (all text meets WCAG AA)

## Implementation Notes

**Files to modify:**
- `/app/announcements/page.tsx` - Main component
- `/app/globals.css` - Update color variables and utility classes
- No new dependencies required

**CSS approach:**
- Use Tailwind utility classes where possible
- Add custom CSS for sticky columns and grid layout
- Keep existing Material Design classes

**React patterns:**
- Use `useState` for expand/collapse per row
- Keep existing server component for data fetching
- Add client component wrapper for interactive features

**Performance:**
- No virtualization needed (100 rows is manageable)
- Lazy load expanded content if needed
- CSS containment for scroll performance

## Future Enhancements (Out of Scope)

- Column sorting (click header to sort)
- Column visibility toggles (hide/show columns)
- Export to CSV functionality
- Advanced filtering sidebar
- Mobile-optimized card view
- Keyboard shortcuts (J/K navigation)
- Real-time WebSocket updates (vs 30s polling)

## Success Criteria

1. ✅ Professional, modern appearance (Modern Minimal aesthetic)
2. ✅ Comfortable reading experience (proper spacing, readable text)
3. ✅ Company and title always visible (sticky left columns)
4. ✅ Easy pattern scanning (subtle color coding)
5. ✅ Smooth interactions (expand/collapse, hover states)
6. ✅ All 19 columns accessible (horizontal scroll)
7. ✅ No functionality lost (all existing features preserved)
8. ✅ Same-day deployment possible (incremental approach)
