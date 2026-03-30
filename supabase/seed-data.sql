-- =====================================================
-- TASE Algorithmic Trading System - Seed Data
-- =====================================================
-- Test data for development and testing
-- Created: 2026-03-30
-- Version: 1.0
-- =====================================================

-- =====================================================
-- Seed Data: company_ticker_mapping
-- =====================================================
-- 5 Sample TASE companies across different sectors
-- =====================================================

INSERT INTO company_ticker_mapping (
    tase_company_id,
    ticker,
    company_name_english,
    company_name_hebrew,
    alternative_names,
    sector,
    market_cap_category,
    is_active,
    avg_daily_volume
) VALUES
    (
        'TSEM',
        'TSEM.TA',
        'Tower Semiconductor Ltd.',
        'טאוור סמיקונדקטור בע"מ',
        ARRAY['Tower Semi', 'Tower', 'TowerJazz'],
        'Technology',
        'large',
        TRUE,
        1500000
    ),
    (
        'TEVA',
        'TEVA.TA',
        'Teva Pharmaceutical Industries Ltd.',
        'טבע תעשיות פרמצבטיות בע"מ',
        ARRAY['Teva Pharma', 'Teva', 'Teva Industries'],
        'Pharmaceuticals',
        'large',
        TRUE,
        2000000
    ),
    (
        'ICL',
        'ICL.TA',
        'Israel Chemicals Ltd.',
        'כימיקלים לישראל בע"מ',
        ARRAY['ICL', 'Israel Chemicals', 'ICL Group'],
        'Materials',
        'large',
        TRUE,
        1200000
    ),
    (
        'NICE',
        'NICE.TA',
        'NICE Systems Ltd.',
        'נייס מערכות בע"מ',
        ARRAY['NICE', 'NICE Systems', 'NICE Ltd'],
        'Technology',
        'large',
        TRUE,
        800000
    ),
    (
        'ELCO',
        'ELCO.TA',
        'Elco Holdings Ltd.',
        'אלקו אחזקות בע"מ',
        ARRAY['Elco', 'Elco Holdings', 'Elco Group'],
        'Industrials',
        'medium',
        TRUE,
        300000
    );

-- =====================================================
-- Seed Data: announcements
-- =====================================================
-- 1 Sample announcement for testing
-- =====================================================

INSERT INTO announcements (
    ticker,
    company_name,
    title,
    content,
    tase_url,
    published_at,
    sentiment,
    confidence,
    reasoning,
    should_trade,
    processed
) VALUES (
    'TSEM.TA',
    'Tower Semiconductor Ltd.',
    'Tower Semiconductor Reports Strong Q4 2025 Results',
    'Tower Semiconductor Ltd. announced today fourth quarter 2025 revenues of $420 million, exceeding guidance. GAAP net income was $45 million, or $0.42 per diluted share. Non-GAAP net income was $62 million, or $0.58 per diluted share. The company reported strong demand across all business segments and raised guidance for Q1 2026.',
    'https://maya.tase.co.il/reports/details/1234567',
    NOW() - INTERVAL '2 hours',
    'positive',
    0.8750,
    'Strong revenue beat, raised guidance, positive momentum across segments',
    TRUE,
    TRUE
);

-- =====================================================
-- Seed Data: system_logs
-- =====================================================
-- 2 Sample log entries
-- =====================================================

INSERT INTO system_logs (
    log_level,
    component,
    message,
    metadata
) VALUES
    (
        'INFO',
        'announcement_checker',
        'Successfully fetched and processed 5 new announcements',
        '{"fetch_time_ms": 1250, "new_announcements": 5, "processed": 5}'::JSONB
    ),
    (
        'INFO',
        'position_monitor',
        'Updated prices for 3 open positions',
        '{"update_time_ms": 850, "positions_updated": 3, "api_calls": 3}'::JSONB
    );

-- =====================================================
-- Seed Data Loading Complete
-- =====================================================
-- Database is ready for testing
-- =====================================================
