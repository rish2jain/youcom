-- Migration: Add usage tracking and user actions tables
-- Date: 2025-10-30
-- Description: Support real API usage tracking and user-generated actions

-- API Usage Tracking
CREATE TABLE IF NOT EXISTS api_usage_logs (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(50) NOT NULL,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    status_code INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    cost_estimate DECIMAL(10, 4) DEFAULT 0,
    user_id INTEGER,
    request_size INTEGER,
    response_size INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User Actions
CREATE TABLE IF NOT EXISTS user_actions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'Medium',
    status VARCHAR(20) DEFAULT 'Pending',
    assignee VARCHAR(100),
    due_date DATE,
    source VARCHAR(100),
    tags TEXT[], -- PostgreSQL array type
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Watch Items (enhanced)
CREATE TABLE IF NOT EXISTS watch_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    competitor_name VARCHAR(100) NOT NULL,
    keywords TEXT[],
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_checked TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    latest_activity TEXT,
    impact_cards_generated INTEGER DEFAULT 0
);

-- Research Reports (enhanced)
CREATE TABLE IF NOT EXISTS research_reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    company_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'processing',
    summary TEXT,
    total_sources INTEGER DEFAULT 0,
    confidence_score INTEGER DEFAULT 0,
    search_results JSONB,
    research_report JSONB,
    api_usage JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Impact Cards
CREATE TABLE IF NOT EXISTS impact_cards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    watch_item_id INTEGER REFERENCES watch_items(id),
    title VARCHAR(200) NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    impact_areas TEXT[],
    timeline VARCHAR(100),
    confidence INTEGER,
    sources INTEGER,
    key_insights TEXT,
    timeline_events JSONB,
    recommended_actions JSONB,
    source_breakdown JSONB,
    processing_details JSONB,
    news_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_created_at ON api_usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_api_name ON api_usage_logs(api_name);
CREATE INDEX IF NOT EXISTS idx_user_actions_status ON user_actions(status);
CREATE INDEX IF NOT EXISTS idx_user_actions_priority ON user_actions(priority);
CREATE INDEX IF NOT EXISTS idx_watch_items_active ON watch_items(is_active);
CREATE INDEX IF NOT EXISTS idx_research_reports_status ON research_reports(status);
CREATE INDEX IF NOT EXISTS idx_impact_cards_risk_level ON impact_cards(risk_level);

-- Update triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_actions_updated_at BEFORE UPDATE ON user_actions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_impact_cards_updated_at BEFORE UPDATE ON impact_cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();