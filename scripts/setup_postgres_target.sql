-- ============================================================
-- Target PostgreSQL Databases (port 54322)
-- apollo_analytics & apollo_financial
-- ============================================================

-- Create databases
CREATE DATABASE apollo_analytics;
CREATE DATABASE apollo_financial;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE apollo_analytics TO sentinelsql;
GRANT ALL PRIVILEGES ON DATABASE apollo_financial TO sentinelsql;
