-- =====================================================
-- Trigger Test: Auto-Queue New Announcements
-- =====================================================
-- Tests that new announcements are automatically added
-- to the processing queue when inserted
-- =====================================================

-- Test trigger: Insert announcement and verify queue entry
BEGIN;

INSERT INTO announcements (
  ticker, company_name, title, content, published_at, processed, tase_url
) VALUES (
  'TRIGTEST', 'Trigger Test Corp', 'Test Title', 'Test Content', NOW(), false,
  'https://example.com/test-' || gen_random_uuid()
);

-- Check queue entry was created
SELECT COUNT(*) AS queue_entry_count FROM announcement_processing_queue
WHERE announcement_id = (
  SELECT id FROM announcements
  WHERE ticker = 'TRIGTEST'
  ORDER BY created_at DESC LIMIT 1
);
-- Expected: 1

-- Check status is 'pending'
SELECT status FROM announcement_processing_queue
WHERE announcement_id = (
  SELECT id FROM announcements
  WHERE ticker = 'TRIGTEST'
  ORDER BY created_at DESC LIMIT 1
);
-- Expected: 'pending'

ROLLBACK;  -- Clean up test data
