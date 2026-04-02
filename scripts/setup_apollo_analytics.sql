-- ============================================================
-- apollo_analytics Database Tables (PostgreSQL)
-- ============================================================

CREATE TABLE IF NOT EXISTS encounter_summaries (
    summary_id SERIAL PRIMARY KEY,
    facility_id VARCHAR(20),
    facility_name VARCHAR(200),
    department_id VARCHAR(20),
    department_name VARCHAR(100),
    encounter_type VARCHAR(50),
    report_month DATE,
    total_encounters INT DEFAULT 0,
    total_admissions INT DEFAULT 0,
    total_discharges INT DEFAULT 0,
    avg_length_of_stay DECIMAL(6,2),
    bed_occupancy_rate DECIMAL(5,2),
    mortality_count INT DEFAULT 0,
    mortality_rate DECIMAL(5,4),
    readmission_count INT DEFAULT 0,
    readmission_rate DECIMAL(5,4),
    total_revenue DECIMAL(14,2),
    avg_revenue_per_encounter DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS population_health (
    record_id SERIAL PRIMARY KEY,
    report_quarter VARCHAR(10),
    region VARCHAR(100),
    age_group VARCHAR(20),
    gender VARCHAR(10),
    disease_category VARCHAR(100),
    patient_count INT DEFAULT 0,
    encounter_count INT DEFAULT 0,
    avg_cost DECIMAL(10,2),
    avg_los DECIMAL(6,2),
    mortality_rate DECIMAL(5,4),
    complication_rate DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quality_metrics (
    metric_id SERIAL PRIMARY KEY,
    facility_id VARCHAR(20),
    department_id VARCHAR(20),
    metric_name VARCHAR(200),
    metric_category VARCHAR(50),
    report_month DATE,
    numerator INT,
    denominator INT,
    metric_value DECIMAL(10,4),
    target_value DECIMAL(10,4),
    benchmark_value DECIMAL(10,4),
    performance_status VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS research_cohorts (
    cohort_id SERIAL PRIMARY KEY,
    study_name VARCHAR(200),
    pi_name VARCHAR(100),
    irb_number VARCHAR(50),
    start_date DATE,
    end_date DATE,
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant schema permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO sentinelsql;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sentinelsql;
