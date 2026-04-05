# TASE Trading Dashboard - Design Guidelines

**Reference Page:** https://tase-trading-dashboard.vercel.app/announcements

These guidelines ensure consistent design across all pages in the TASE Trading Dashboard.

---

## 🎨 Design Philosophy

**Clean, Professional, Data-Dense** - Focus on information clarity with subtle visual enhancements. No decorative elements, only functional design.

---

## 📏 Layout Structure

### Page Container
```tsx
<div>
  {/* Page header */}
  {/* Stats cards */}
  {/* Filter/search section */}
  {/* Main content (table/cards) */}
</div>
```

### Spacing
- **Page top margin:** `0` (no top margin)
- **Section bottom margin:** `24px` between sections
- **Stats grid margin:** `32px` bottom
- **Container max-width:** `max-w-7xl` (handled by layout)
- **Container padding:** `px-6 py-8` (handled by layout)

---

## 📝 Typography

### Page Header
```tsx
<div style={{ marginBottom: '24px' }}>
  <h1 style={{
    fontSize: '28px',
    fontWeight: 'bold',
    marginBottom: '8px'
  }}>Page Title</h1>
  <p style={{
    color: '#666',
    fontSize: '14px'
  }}>Descriptive subtitle</p>
</div>
```

### Font Sizes
- **Page title:** `28px`, bold
- **Card title:** `36px`, bold (stat numbers)
- **Card label:** `11px`, bold, uppercase, letter-spacing: 0.5px
- **Body text:** `14px`
- **Small text:** `11px-13px`
- **Table headers:** `12px`, bold, uppercase, letter-spacing: 0.5px

---

## 🎴 Stat Cards

### Grid Layout
```tsx
<div style={{
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
  gap: '20px',
  marginBottom: '32px'
}}>
```

### Card Structure
```tsx
<div style={{
  background: 'white',
  borderRadius: '8px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  borderLeft: '4px solid #3b82f6',  // Accent color
  padding: '24px'
}}>
  <div style={{
    color: '#6b7280',
    fontSize: '11px',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    marginBottom: '12px'
  }}>LABEL</div>
  <div style={{
    fontSize: '36px',
    fontWeight: 'bold',
    color: '#111827'
  }}>VALUE</div>
</div>
```

### Accent Colors for Left Border
- **Blue:** `#3b82f6` - General/total metrics
- **Green:** `#10b981` - Positive/success metrics
- **Purple:** `#8b5cf6` - Processed/completed metrics
- **Orange:** `#f59e0b` - Pending/warning metrics
- **Red:** `#ef4444` - Error/negative metrics

---

## 🔍 Filter/Search Section

### Container
```tsx
<div style={{
  background: 'white',
  borderRadius: '8px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  padding: '24px',
  marginBottom: '24px'
}}>
```

### Input Fields
```tsx
<input
  type="text"
  placeholder="🔍 Search..."
  style={{
    width: '100%',
    padding: '10px 16px',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '14px'
  }}
/>
```

### Select Dropdowns
```tsx
<select style={{
  padding: '10px 16px',
  border: '1px solid #d1d5db',
  borderRadius: '8px',
  background: 'white',
  fontSize: '14px',
  cursor: 'pointer'
}}>
```

---

## 📊 Tables

### Container (Horizontally Scrollable)
```tsx
<div style={{
  background: 'white',
  borderRadius: '8px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  overflow: 'hidden'
}}>
  <div style={{ overflowX: 'auto', scrollBehavior: 'smooth', maxWidth: '100%' }}>
    <table style={{ width: 'max-content', minWidth: '100%', borderCollapse: 'collapse' }}>
```

**Key properties for horizontal scrolling:**
- Container: `overflowX: 'auto'` + `maxWidth: '100%'`
- Table: `width: 'max-content'` + `minWidth: '100%'`
- This ensures table scrolls horizontally when content exceeds viewport

### Table Headers (Generous Spacing)
```tsx
<thead style={{ background: '#f9fafb' }}>
  <tr>
    <th style={{
      padding: '16px 20px',  // Bigger padding for spacious feel
      textAlign: 'right',  // Or 'left', 'center'
      fontSize: '12px',
      fontWeight: 600,
      color: '#6b7280',
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
      whiteSpace: 'nowrap',
      minWidth: '100px',  // Ensures minimum column width
      borderBottom: '1px solid #e5e7eb'  // Subtle 1px border
    }}>HEADER</th>
  </tr>
</thead>
```

**Padding:** `16px 20px` (vertical horizontal) - more spacious than compact tables

**Column sizing guidelines:**
- Narrow columns (serial numbers, checkboxes): `minWidth: '80px'`
- Medium columns (dates, numbers, short text): `minWidth: '100-180px'`
- Wide columns (titles, names): `minWidth: '200-300px'`
- Extra-wide columns (content, descriptions): `minWidth: '400px'`

### Sticky Columns (for wide scrollable tables)
```tsx
<th style={{
  position: 'sticky',
  left: 0,  // First sticky column at left: 0
  // left: '80px',  // Second sticky column (after 80px first column)
  // left: '260px',  // Third sticky column (after 80px + 180px)
  background: '#f9fafb',
  zIndex: 10,
  minWidth: '80px',
  padding: '16px 20px',
  // ... other th styles
  borderRight: '1px solid #e5e7eb'  // Visual separator
}}>
```

**Sticky column positioning:**
- Calculate `left` by summing widths of all previous sticky columns
- Example: Column 1 (80px) → Column 2 left: '80px' → Column 3 left: '260px' (80+180)
- Always set `background` to match header/row background
- Use `borderRight` with thicker border (2px) on last sticky column for clear separation

### Table Body
```tsx
<tbody style={{ background: 'white' }}>
```

### Table Row Hover
```tsx
<tr
  style={{ transition: 'background-color 0.15s ease' }}
  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f9fafb'}
  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
>
```

### Table Cells (Generous Spacing)
```tsx
<td style={{
  padding: '20px 16px',  // Bigger padding matching headers
  fontSize: '14px',
  color: '#111827',  // Or '#6b7280' for secondary text
  textAlign: 'right',  // Match header alignment
  minWidth: '100px',  // Match header minWidth
  borderBottom: '1px solid #e5e7eb'
}}>
```

**Cell padding:** `20px 16px` (vertical horizontal) - matches header padding for consistent spacing

---

## 🏷️ Badges (Sentiment/Status)

### Badge Structure
```tsx
<span style={{
  padding: '6px 12px',
  borderRadius: '6px',
  fontSize: '11px',
  fontWeight: 500,
  textTransform: 'uppercase',
  letterSpacing: '0.025em',
  display: 'inline-block',
  // Color combinations below
}}>
  LABEL
</span>
```

### Badge Colors
**Positive/Success (Green):**
```tsx
background: '#dcfce7',
color: '#16a34a',
border: '1px solid #bbf7d0'
```

**Negative/Danger (Red):**
```tsx
background: '#fee2e2',
color: '#dc2626',
border: '1px solid #fecaca'
```

**Neutral/Info (Blue):**
```tsx
background: '#dbeafe',
color: '#2563eb',
border: '1px solid #bfdbfe'
```

**Pending/Warning (Yellow-Orange):**
```tsx
background: '#fef3c7',
color: '#d97706',
border: '1px solid #fde68a'
```

---

## 🎨 Color Palette

### Backgrounds
- **Page background:** `#f8f9fa` (set in globals.css)
- **Card/Container background:** `white`
- **Table header background:** `#f9fafb`
- **Hover background:** `#f9fafb`

### Borders
- **Default border:** `1px solid #e5e7eb`
- **Strong border:** `2px solid #e5e7eb`
- **Separator border:** `1px solid #d1d5db`
- **Accent border (cards):** `4px solid [color]`

### Text Colors
- **Primary text:** `#111827`
- **Secondary text:** `#6b7280`
- **Muted text:** `#9ca3af`
- **Light text:** `#666`

### Shadows
- **Default card shadow:** `0 1px 3px rgba(0,0,0,0.1)`
- **Elevated card shadow:** `0 4px 6px rgba(0,0,0,0.1)`

---

## 🔘 Interactive Elements

### Buttons (if needed)
```tsx
<button style={{
  padding: '10px 16px',
  borderRadius: '8px',
  border: '1px solid #d1d5db',
  background: 'white',
  fontSize: '14px',
  cursor: 'pointer',
  transition: 'background-color 0.15s'
}}>
```

### Links
```tsx
<a style={{
  color: '#2563eb',
  cursor: 'pointer',
  fontWeight: 500,
  fontSize: '13px',
  textDecoration: 'none',
  transition: 'color 0.15s'
}}
onMouseEnter={(e) => e.currentTarget.style.color = '#1d4ed8'}
onMouseLeave={(e) => e.currentTarget.style.color = '#2563eb'}
>
```

---

## 📐 Border Radius Standards

- **Cards/Containers:** `8px`
- **Inputs/Selects:** `8px`
- **Badges:** `6px`
- **Buttons:** `8px`
- **Pills (status indicators):** `999px` (fully rounded)

---

## 🚫 What NOT to Include

❌ **No decorative icons** (chart icons, trend icons, etc.)
❌ **No gradient backgrounds** on cards (only white backgrounds with colored left borders)
❌ **No large icons** anywhere (all icons must be inline-styled to exact pixels)
❌ **No Tailwind utility classes** for sizing (use inline styles: `style={{width: 'Xpx', height: 'Xpx'}}`)
❌ **No complex animations** (only simple hover transitions)

---

## ✅ Icon Guidelines

If icons are absolutely necessary:

```tsx
<svg style={{
  width: '16px',   // Small: 12-16px
  height: '16px',  // Medium: 20px
  // Large (empty states only): 64px
}} fill="none" stroke="currentColor" viewBox="0 0 24 24">
  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="..." />
</svg>
```

**Preferred:** Use emoji or text labels instead of icons where possible.

---

## 📱 Responsive Grid

```tsx
<div style={{
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',  // Cards
  // OR
  gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',  // Wider cards
  gap: '20px'
}}>
```

---

## 🎯 Empty States

```tsx
<div style={{
  textAlign: 'center',
  padding: '48px 24px',
  color: '#6b7280'
}}>
  <svg style={{
    width: '64px',
    height: '64px',
    color: '#d1d5db',
    margin: '0 auto 16px'
  }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    {/* Icon path */}
  </svg>
  <p style={{ fontWeight: 500, marginBottom: '4px' }}>No data yet</p>
  <p style={{ fontSize: '14px', color: '#9ca3af' }}>Data will appear here automatically</p>
</div>
```

---

## 📋 Implementation Checklist

When creating/updating a page:

- [ ] Page header with title (28px bold) and subtitle (14px #666)
- [ ] Stats cards grid with colored left borders
- [ ] White background cards with subtle shadow
- [ ] 24px margin between sections
- [ ] All icons use inline styles (no Tailwind classes)
- [ ] Table with #f9fafb header background
- [ ] Border radius: 8px for all cards/containers
- [ ] Hover effects on interactive elements
- [ ] Consistent padding: 24px for cards, 12px for table cells
- [ ] Color-coded badges for status/sentiment
- [ ] Empty states with centered text and optional icon

---

## 🔗 Related Files

- **Layout:** `/app/layout.tsx` - Navigation and footer
- **Reference Page:** `/app/announcements/page.tsx`
- **Global Styles:** `/app/globals.css`

---

**Last Updated:** 2026-04-05
**Reference:** https://tase-trading-dashboard.vercel.app/announcements
