# Page Redesign Prompt Template

Use this template when asking Claude to redesign a page to match the TASE Trading Dashboard design standards.

---

## 📝 Template

```
Please redesign the [PAGE_NAME] page to match our design guidelines.

**Reference page:** https://tase-trading-dashboard.vercel.app/announcements
**Guidelines:** docs/DESIGN_GUIDELINES.md
**Target page file:** [FILE_PATH]

### Requirements:

1. **Layout Structure:**
   - Page header (28px bold title + 14px subtitle)
   - Stats cards grid (if applicable)
   - Filter/search section (if applicable)
   - Main content area (table or cards)

2. **Design Standards:**
   - White cards with 8px border radius
   - Subtle shadow: 0 1px 3px rgba(0,0,0,0.1)
   - 24px spacing between sections
   - Colored left borders on stat cards (4px solid)

3. **Colors:**
   - Background: white for cards
   - Text: #111827 (primary), #6b7280 (secondary)
   - Borders: #e5e7eb (default), #d1d5db (separator)

4. **NO Tailwind classes for sizing** - use inline styles:
   - Icons: style={{width: 'Xpx', height: 'Xpx'}}
   - All dimensions must be explicit pixels

5. **Keep existing:**
   - Data fetching logic
   - Component structure
   - All data columns/fields

6. **Change only:**
   - Visual styling (colors, spacing, borders)
   - Layout structure
   - Typography

### Current Issues (if any):
[Describe what's wrong with the current page - e.g., "huge icons", "inconsistent spacing", "missing cards"]

### Specific Requests:
[Any specific requirements - e.g., "add 4 stat cards at the top", "make the table scrollable horizontally"]

Please follow the DESIGN_GUIDELINES.md exactly.
```

---

## 🎯 Example Usage

### Example 1: Dashboard Page

```
Please redesign the Dashboard page to match our design guidelines.

**Reference page:** https://tase-trading-dashboard.vercel.app/announcements
**Guidelines:** docs/DESIGN_GUIDELINES.md
**Target page file:** app/page.tsx

### Requirements:

1. **Layout Structure:**
   - Page header "TASE Trading Dashboard" (28px) + subtitle
   - 4 stat cards: Total Positions, Total P/L, Win Rate, Avg Hold Time
   - Two-column grid: Recent Announcements | Recent Positions
   - AI-Powered Sentiment Trading info section

2. **Design Standards:**
   - Match announcements page exactly
   - White cards with subtle shadow
   - Stats cards with colored left borders:
     - Blue (#3b82f6) for Total Positions
     - Green (#10b981) for Total P/L (if positive)
     - Purple (#8b5cf6) for Win Rate
     - Orange (#f59e0b) for Avg Hold Time

3. **Keep existing:**
   - All data fetching (getDashboardData)
   - Position and announcement lists
   - Empty states

4. **Change only:**
   - Visual styling to match announcements page
   - Remove any decorative icons
   - Consistent spacing and typography

### Current Issues:
- Inconsistent card styling
- Some decorative elements remain
- Spacing doesn't match announcements page

Please follow the DESIGN_GUIDELINES.md exactly.
```

### Example 2: Positions Page

```
Please redesign the Positions page to match our design guidelines.

**Reference page:** https://tase-trading-dashboard.vercel.app/announcements
**Guidelines:** docs/DESIGN_GUIDELINES.md
**Target page file:** app/positions/page.tsx

### Requirements:

1. **Layout Structure:**
   - Page header "Positions" + subtitle
   - 4 stat cards (if applicable)
   - Filter section (optional)
   - Table with position data

2. **Design Standards:**
   - Exact match to announcements page table style
   - Table header: #f9fafb background
   - Hover effect on rows
   - Badges for status (OPEN/CLOSED)

3. **Colors:**
   - Profit/Loss text: green (#16a34a) for positive, red (#dc2626) for negative
   - Status badges: blue (#2563eb) for OPEN, gray for CLOSED

4. **Keep existing:**
   - All position data columns
   - Sorting/filtering logic (if any)

### Current Issues:
- Table doesn't match design guidelines
- Inconsistent badge styling

Please follow the DESIGN_GUIDELINES.md exactly.
```

---

## 🚀 Quick Redesign Request

For a quick request without full details:

```
Redesign [PAGE_NAME] to match the announcements page design.
Reference: docs/DESIGN_GUIDELINES.md
Target: [FILE_PATH]
```

---

## ✅ After Redesign Checklist

Ask Claude to verify:

- [ ] Page header matches (28px title, 14px subtitle)
- [ ] All cards have white background + subtle shadow
- [ ] Stat cards have colored left borders (4px)
- [ ] 24px spacing between sections
- [ ] All icons use inline styles (no Tailwind sizing classes)
- [ ] Table headers use #f9fafb background
- [ ] Consistent border radius (8px)
- [ ] Hover effects work
- [ ] Empty states styled correctly
- [ ] Colors match palette in guidelines

---

**Related Files:**
- Design Guidelines: `docs/DESIGN_GUIDELINES.md`
- Reference Page: `/app/announcements/page.tsx`
- Layout: `/app/layout.tsx`
