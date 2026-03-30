-- =====================================================
-- TASE Algorithmic Trading System - Database Schema
-- =====================================================
-- PostgreSQL schema for Supabase backend
-- Created: 2026-03-30
-- Version: 1.0
-- =====================================================

-- Drop existing tables if they exist (for clean re-creation)
DROP TABLE IF EXISTS system_status CASCADE;
DROP TABLE IF EXISTS unmapped_companies CASCADE;
DROP TABLE IF EXISTS system_logs CASCADE;
DROP TABLE IF EXISTS positions CASCADE;
DROP TABLE IF EXISTS announcements CASCADE;
DROP TABLE IF EXISTS company_ticker_mapping CASCADE;

-- Drop existing functions if they exist
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- =====================================================
-- Table 1: announcements
-- =====================================================
-- Stores TASE announcements with sentiment analysis
-- Primary entity for trading signals
-- =====================================================

CREATE TABLE announcements (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Ticker and Company Information
    ticker VARCHAR(20) NOT NULL,
    company_name VARCHAR(255) NOT NULL,

    -- Announcement Content
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tase_url TEXT NOT NULL UNIQUE,

    -- Timing
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Sentiment Analysis (from Claude API)
    sentiment VARCHAR(20) CHECK (sentiment IN ('positive', 'negative', 'neutral', 'mixed')),
    confidence NUMERIC(5,4) CHECK (confidence >= 0 AND confidence <= 1),
    reasoning TEXT,
    should_trade BOOLEAN DEFAULT FALSE,

    -- Processing Status
    processed BOOLEAN DEFAULT FALSE,
    error_message TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for announcements table
CREATE INDEX idx_announcements_ticker ON announcements(ticker);
CREATE INDEX idx_announcements_published_at ON announcements(published_at DESC);
CREATE INDEX idx_announcements_processed ON announcements(processed) WHERE NOT processed;
CREATE INDEX idx_announcements_should_trade ON announcements(should_trade) WHERE should_trade = TRUE;

-- =====================================================
-- Table 2: positions
-- =====================================================
-- Tracks trading positions lifecycle from entry to exit
-- Includes profit/loss calculation and error handling
-- =====================================================

CREATE TABLE positions (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key to Announcement
    announcement_id UUID NOT NULL REFERENCES announcements(id) ON DELETE CASCADE,

    -- Position Identification
    ticker VARCHAR(20) NOT NULL,

    -- Entry Details
    entry_price NUMERIC(12,4) NOT NULL CHECK (entry_price > 0),
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),

    -- Exit Details (NULL until position is closed)
    exit_price NUMERIC(12,4) CHECK (exit_price > 0),
    exit_time TIMESTAMP WITH TIME ZONE,
    exit_reason VARCHAR(50) CHECK (exit_reason IN ('take_profit', 'stop_loss', 'manual', 'timeout')),

    -- Position Tracking
    peak_price NUMERIC(12,4) CHECK (peak_price > 0),
    peak_time TIMESTAMP WITH TIME ZONE,
    current_price NUMERIC(12,4) CHECK (current_price > 0),
    last_price_update TIMESTAMP WITH TIME ZONE,

    -- Profit/Loss Calculation
    profit_loss NUMERIC(12,2),
    profit_loss_percentage NUMERIC(8,4),

    -- Position Status
    status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed', 'error')),

    -- Error Handling
    error_message TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for positions table
CREATE INDEX idx_positions_ticker ON positions(ticker);
CREATE INDEX idx_positions_status ON positions(status) WHERE status = 'open';
CREATE INDEX idx_positions_announcement_id ON positions(announcement_id);
CREATE INDEX idx_positions_entry_time ON positions(entry_time DESC);

-- =====================================================
-- Table 3: company_ticker_mapping
-- =====================================================
-- Reference table mapping TASE companies to tickers
-- Supports fuzzy matching and alternative names
-- =====================================================

CREATE TABLE company_ticker_mapping (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- TASE Identification
    tase_company_id VARCHAR(50) UNIQUE,
    ticker VARCHAR(20) NOT NULL UNIQUE,

    -- Company Names
    company_name_english VARCHAR(255) NOT NULL,
    company_name_hebrew VARCHAR(255),
    alternative_names TEXT[], -- Array for fuzzy matching

    -- Trading Information
    sector VARCHAR(100),
    market_cap_category VARCHAR(50) CHECK (market_cap_category IN ('large', 'medium', 'small', 'micro')),

    -- Activity Tracking
    is_active BOOLEAN DEFAULT TRUE,
    avg_daily_volume INTEGER,
    last_traded_date DATE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for company_ticker_mapping table
CREATE INDEX idx_company_ticker ON company_ticker_mapping(ticker);
CREATE INDEX idx_company_name_english ON company_ticker_mapping(company_name_english);
CREATE INDEX idx_company_is_active ON company_ticker_mapping(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_company_sector ON company_ticker_mapping(sector);

-- Full-text search index for fuzzy matching
CREATE INDEX idx_company_names_fulltext ON company_ticker_mapping
    USING GIN (to_tsvector('english', company_name_english || ' ' || COALESCE(company_name_hebrew, '')));

-- =====================================================
-- Table 4: system_logs
-- =====================================================
-- Audit trail for system operations
-- Stores logs from all components with metadata
-- =====================================================

CREATE TABLE system_logs (
    -- Primary Key (BIGSERIAL for high-volume logs)
    id BIGSERIAL PRIMARY KEY,

    -- Log Details
    log_level VARCHAR(20) NOT NULL CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    component VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,

    -- Additional Context
    metadata JSONB,

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for system_logs table
CREATE INDEX idx_system_logs_level ON system_logs(log_level);
CREATE INDEX idx_system_logs_component ON system_logs(component);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at DESC);

-- =====================================================
-- Table 5: unmapped_companies
-- =====================================================
-- Queue for manual review of unmapped company names
-- Populated when ticker mapping fails
-- =====================================================

CREATE TABLE unmapped_companies (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Company Information from Announcement
    company_name_from_announcement VARCHAR(255) NOT NULL,
    announcement_title TEXT,
    announcement_url TEXT,

    -- Review Status
    reviewed BOOLEAN DEFAULT FALSE,
    resolved_ticker VARCHAR(20),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for unmapped_companies table
CREATE INDEX idx_unmapped_reviewed ON unmapped_companies(reviewed) WHERE NOT reviewed;

-- =====================================================
-- Table 6: system_status
-- =====================================================
-- Singleton table for system health monitoring
-- Only one row (id = 1) exists at all times
-- =====================================================

CREATE TABLE system_status (
    -- Primary Key (Singleton: only id = 1 allowed)
    id INTEGER PRIMARY KEY CHECK (id = 1),

    -- System State
    is_running BOOLEAN DEFAULT FALSE,
    last_announcement_check TIMESTAMP WITH TIME ZONE,
    last_position_update TIMESTAMP WITH TIME ZONE,

    -- Error Tracking
    error_count INTEGER DEFAULT 0,
    last_error TEXT,

    -- Metadata
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default singleton row
INSERT INTO system_status (id, is_running, error_count)
VALUES (1, FALSE, 0)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- Trigger Function: Auto-update updated_at timestamp
-- =====================================================
-- Automatically updates the updated_at column on row modification
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Triggers: Apply auto-update to tables with updated_at
-- =====================================================

-- Trigger for announcements table
CREATE TRIGGER trigger_announcements_updated_at
    BEFORE UPDATE ON announcements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for positions table
CREATE TRIGGER trigger_positions_updated_at
    BEFORE UPDATE ON positions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for company_ticker_mapping table
CREATE TRIGGER trigger_company_ticker_mapping_updated_at
    BEFORE UPDATE ON company_ticker_mapping
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for system_status table
CREATE TRIGGER trigger_system_status_updated_at
    BEFORE UPDATE ON system_status
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Schema Creation Complete
-- =====================================================
-- Next step: Load seed data from seed-data.sql
-- =====================================================
