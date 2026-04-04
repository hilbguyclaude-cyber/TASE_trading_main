-- =====================================================
-- Migration: Add attached_files column to announcements
-- =====================================================
-- Date: 2026-04-04
-- Purpose: Store URLs of attached PDF/PPT files from TASE announcements
-- =====================================================

-- Add attached_files column as JSONB
-- Structure: Array of file objects
-- Example:
-- [
--   {
--     "name": "presentation_march_2026.pdf",
--     "url": "https://mayafiles.tase.co.il/.../file.pdf",
--     "type": "pdf"
--   },
--   {
--     "name": "financial_report.pptx",
--     "url": "https://mayafiles.tase.co.il/.../file.pptx",
--     "type": "pptx"
--   }
-- ]

ALTER TABLE announcements
ADD COLUMN attached_files JSONB DEFAULT '[]'::jsonb;

-- Add index for querying announcements with files
CREATE INDEX idx_announcements_with_files
ON announcements((jsonb_array_length(attached_files)))
WHERE jsonb_array_length(attached_files) > 0;

-- Add comment for documentation
COMMENT ON COLUMN announcements.attached_files IS 'Array of attached file objects with name, url, and type';
