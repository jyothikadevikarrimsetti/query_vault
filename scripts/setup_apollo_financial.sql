-- ============================================================
-- apollo_financial Database Tables (PostgreSQL)
-- ============================================================

CREATE TABLE IF NOT EXISTS claims (
    claim_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    encounter_id INT,
    claim_type VARCHAR(30),
    total_amount DECIMAL(12,2),
    insurance_id VARCHAR(50),
    facility_id VARCHAR(20),
    submitted_date DATE,
    adjudicated_date DATE,
    status VARCHAR(30) DEFAULT 'submitted',
    denial_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS claim_line_items (
    line_item_id SERIAL PRIMARY KEY,
    claim_id INT NOT NULL,
    procedure_code VARCHAR(20),
    description TEXT,
    quantity INT DEFAULT 1,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    modifier VARCHAR(10),
    service_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
);

CREATE TABLE IF NOT EXISTS insurance_plans (
    plan_id SERIAL PRIMARY KEY,
    plan_name VARCHAR(200),
    payer_name VARCHAR(200),
    plan_type VARCHAR(50),
    coverage_start DATE,
    coverage_end DATE,
    premium DECIMAL(10,2),
    deductible DECIMAL(10,2),
    copay DECIMAL(8,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patient_billing (
    billing_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    encounter_id INT,
    total_charges DECIMAL(12,2),
    insurance_paid DECIMAL(12,2),
    patient_responsibility DECIMAL(10,2),
    payment_status VARCHAR(30) DEFAULT 'pending',
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payer_contracts (
    contract_id SERIAL PRIMARY KEY,
    payer_name VARCHAR(200),
    contract_type VARCHAR(50),
    effective_date DATE,
    termination_date DATE,
    reimbursement_rate DECIMAL(5,4),
    fee_schedule TEXT,
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY,
    claim_id INT,
    patient_id INT,
    amount DECIMAL(12,2),
    payment_method VARCHAR(30),
    payment_date DATE,
    reference_number VARCHAR(50),
    payer_type VARCHAR(30),
    status VARCHAR(30) DEFAULT 'processed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant schema permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO sentinelsql;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sentinelsql;
