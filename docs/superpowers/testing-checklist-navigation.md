# Navigation Redesign Testing Checklist

**Date:** 2026-04-05
**Feature:** Navigation Redesign to Layout 2 Style
**Spec:** [2026-04-05-navigation-redesign-design.md](./specs/2026-04-05-navigation-redesign-design.md)

## Automated Checks

- [ ] **TypeScript compilation passes** (`npx tsc --noEmit`)
- [ ] **Production build succeeds** (`npm run build`)
- [ ] **No console errors** in build output

## Visual Regression Testing

- [ ] Compare before/after screenshots of navigation bar
- [ ] Verify navigation matches Layout 2 style (text-only, horizontal)
- [ ] Check logo displays only "TASE Trading" (no subtitle)
- [ ] Verify no LIVE indicator is present
- [ ] Check link spacing and alignment
- [ ] Verify colors match design spec:
  - Background: White (#ffffff)
  - Border: Gray-200 (#e5e7eb)
  - Logo: Dark gray (#111827)
  - Links default: Gray-600 (#6b7280)
  - Links hover: Blue-600 (#2563eb)
  - Links active: Gray-900 (#111827)
- [ ] Test hover states on all 8 navigation links
- [ ] Verify active state shows correctly on announcements page

## Functional Testing

### Navigation Links
- [ ] Click "Home" → redirects to announcements
- [ ] Click "Dashboard" → shows placeholder page
- [ ] Click "Announcements" → shows announcements table
- [ ] Click "Positions" → shows placeholder page
- [ ] Click "Intraday" → shows placeholder page
- [ ] Click "Tickers" → shows placeholder page
- [ ] Click "System" → shows placeholder page
- [ ] Click "Monitoring" → shows placeholder page

### Redirect Behavior
- [ ] Navigate to `/` → instantly redirects to `/announcements`
- [ ] No flash of content during redirect
- [ ] URL bar updates correctly
- [ ] Browser history works correctly (back/forward buttons)

### Placeholder Pages
- [ ] Each placeholder page displays correct title
- [ ] "Coming Soon" message visible
- [ ] Description text renders correctly
- [ ] "Back to Home" button present and styled
- [ ] Clicking "Back to Home" returns to announcements
- [ ] Content is centered both vertically and horizontally

### Active State Logic
- [ ] "Home" link highlighted when on `/` or `/announcements`
- [ ] Active link has darker text color
- [ ] Active link has bottom border (blue)
- [ ] Active state updates correctly when navigating
- [ ] Only one link is active at a time

### Announcements Page
- [ ] Announcements table loads correctly
- [ ] All existing functionality unchanged
- [ ] Data fetching works
- [ ] Table scrolling works
- [ ] Row interactions work
- [ ] Frozen columns work (# and company name)

## Responsive Testing

### Desktop (>1024px)
- [ ] All 8 navigation items visible
- [ ] Comfortable spacing between items
- [ ] Logo and nav don't overlap
- [ ] Navigation is horizontally centered/aligned

### Tablet (768px - 1024px)
- [ ] Navigation items visible or scrollable
- [ ] Reduced spacing looks appropriate
- [ ] Logo remains visible
- [ ] Touch targets are adequate

### Mobile (<768px)
- [ ] Logo visible
- [ ] Navigation scrolls horizontally if needed
- [ ] Touch interactions work
- [ ] Placeholder pages render correctly
- [ ] "Back to Home" button is accessible

## Browser Testing

### Chrome
- [ ] Navigation renders correctly
- [ ] Redirect works instantly
- [ ] Active states update correctly
- [ ] Hover effects work
- [ ] No console errors

### Safari
- [ ] Navigation renders correctly (webkit-specific issues)
- [ ] Redirect works
- [ ] Active states work
- [ ] Transitions smooth
- [ ] No console errors

### Firefox
- [ ] Navigation renders correctly
- [ ] All features work
- [ ] Styling consistent
- [ ] No console errors

### Mobile Browsers
- [ ] Test on Safari iOS
- [ ] Test on Chrome Android
- [ ] Navigation accessible
- [ ] Redirect works

## Accessibility Testing

- [ ] Keyboard navigation: Tab through all links
- [ ] Focus states visible on all links
- [ ] Enter key activates links
- [ ] Screen reader announces navigation correctly
- [ ] Screen reader announces current page
- [ ] Semantic HTML used (`<nav>`, `<Link>`)
- [ ] ARIA labels if needed
- [ ] Contrast ratios meet WCAG AA standards

## Performance Testing

- [ ] Redirect is instant (no delay)
- [ ] Page transitions are smooth
- [ ] No layout shift during navigation
- [ ] No unnecessary re-renders
- [ ] Build size hasn't increased significantly

## File Structure Verification

- [ ] `app/layout.tsx` - Modified (navigation updated)
- [ ] `app/page.tsx` - Modified (redirect added)
- [ ] `app/announcements/page.tsx` - Unchanged
- [ ] `app/dashboard/page.tsx` - Created (placeholder)
- [ ] `app/positions/page.tsx` - Created (placeholder)
- [ ] `app/intraday/page.tsx` - Created (placeholder)
- [ ] `app/tickers/page.tsx` - Created (placeholder)
- [ ] `app/system/page.tsx` - Created (placeholder)
- [ ] `app/monitoring/page.tsx` - Created (placeholder)

## Success Criteria

All of the following must be true:

1. [ ] Navigation bar matches Layout 2 style (text-only, clean horizontal)
2. [ ] Logo shows only "TASE Trading" (no subtitle, no LIVE indicator)
3. [ ] All 8 navigation items visible and clickable
4. [ ] Home page (/) redirects to announcements instantly
5. [ ] "Home" link highlighted when on announcements page
6. [ ] Placeholder pages show "Coming Soon" with back button
7. [ ] Announcements page works exactly as before (unchanged)
8. [ ] Smooth hover states on all navigation links
9. [ ] Active states work correctly
10. [ ] No console errors or warnings
11. [ ] Responsive behavior acceptable on mobile/tablet
12. [ ] Works in Chrome, Safari, Firefox

## Notes

- **Manual testing required**: Steps marked with browser/visual testing cannot be automated
- **Priority**: Focus on functional testing first, then visual, then responsive
- **Rollback plan**: If critical issues found, revert to previous navigation
- **Future**: Add automated visual regression tests
