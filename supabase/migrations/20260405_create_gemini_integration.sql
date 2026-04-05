-- =====================================================
-- Gemini Sentiment Integration - Database Schema
-- =====================================================
-- Migration to add queue, audit, and error tracking tables
-- for Gemini API integration
-- Created: 2026-04-05
-- =====================================================

-- =====================================================
-- Table 1: announcement_processing_queue
-- =====================================================
-- Queue table for reliable announcement processing
-- Tracks processing status and retry attempts
-- =====================================================

CREATE TABLE IF NOT EXISTS announcement_processing_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  announcement_id UUID NOT NULL REFERENCES announcements(id) ON DELETE CASCADE,

  -- Processing status: 'pending', 'processing', 'completed', 'failed'
  status VARCHAR(20) DEFAULT 'pending' NOT NULL,

  -- Retry tracking
  retry_count INTEGER DEFAULT 0 NOT NULL,
  error_message TEXT,

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  processed_at TIMESTAMP WITH TIME ZONE,

  -- Foreign key constraint
  CONSTRAINT fk_announcement FOREIGN KEY (announcement_id)
    REFERENCES announcements(id) ON DELETE CASCADE
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_queue_status_created
  ON announcement_processing_queue(status, created_at);

CREATE INDEX IF NOT EXISTS idx_queue_announcement
  ON announcement_processing_queue(announcement_id);

-- =====================================================
-- Table 2: gemini_analyses
-- =====================================================
-- Audit table for all Gemini API responses
-- Stores full response data for debugging and analysis
-- =====================================================

CREATE TABLE IF NOT EXISTS gemini_analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  announcement_id UUID NOT NULL REFERENCES announcements(id) ON DELETE CASCADE,

  -- Parsed response fields
  sentiment VARCHAR(20) NOT NULL,  -- 'positive', 'negative', 'neutral'
  reasoning TEXT NOT NULL,
  confidence NUMERIC(5,4) NULL,    -- Always NULL (prompt doesn't return it)

  -- Full raw JSON response for debugging
  raw_response JSONB NOT NULL,

  -- Performance metadata
  processing_time_ms INTEGER,

  -- Timestamp
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

  -- Foreign key constraint
  CONSTRAINT fk_announcement_analysis FOREIGN KEY (announcement_id)
    REFERENCES announcements(id) ON DELETE CASCADE
);

-- Indexes for queries
CREATE INDEX IF NOT EXISTS idx_gemini_analyses_announcement
  ON gemini_analyses(announcement_id);

CREATE INDEX IF NOT EXISTS idx_gemini_analyses_created
  ON gemini_analyses(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_gemini_analyses_sentiment
  ON gemini_analyses(sentiment);

-- =====================================================
-- Table 3: gemini_errors
-- =====================================================
-- Error tracking table for failed analyses
-- Helps diagnose and monitor API failures
-- =====================================================

CREATE TABLE IF NOT EXISTS gemini_errors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  announcement_id UUID REFERENCES announcements(id) ON DELETE CASCADE,

  -- Error details
  error_type VARCHAR(50),  -- 'timeout', 'network_timeout', 'invalid_json', 'unknown'
  error_message TEXT,

  -- Performance
  processing_time_ms INTEGER,

  -- Timestamp
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_gemini_errors_created
  ON gemini_errors(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_gemini_errors_type
  ON gemini_errors(error_type);

-- =====================================================
-- Migration Complete
-- =====================================================
-- Tables created:
-- 1. announcement_processing_queue - Processing queue with retry logic
-- 2. gemini_analyses - Audit table for successful API responses
-- 3. gemini_errors - Error tracking for failed analyses
-- =====================================================
