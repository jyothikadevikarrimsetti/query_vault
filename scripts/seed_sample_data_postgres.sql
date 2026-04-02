-- ============================================================
-- Sample Data for apollo_analytics (PostgreSQL)
-- ============================================================

-- Encounter Summaries
INSERT INTO encounter_summaries (facility_id, facility_name, department_id, department_name, encounter_type, report_month, total_encounters, total_admissions, total_discharges, avg_length_of_stay, bed_occupancy_rate, mortality_count, mortality_rate, readmission_count, readmission_rate, total_revenue, avg_revenue_per_encounter) VALUES
('FAC-001', 'Apollo Main Hospital', 'DEP-001', 'Cardiology', 'Inpatient', '2026-03-01', 145, 120, 115, 4.2, 85.5, 3, 0.0207, 8, 0.0552, 14500000.00, 100000.00),
('FAC-001', 'Apollo Main Hospital', 'DEP-002', 'Oncology', 'Inpatient', '2026-03-01', 89, 75, 68, 7.5, 78.2, 5, 0.0562, 4, 0.0449, 13350000.00, 150000.00),
('FAC-001', 'Apollo Main Hospital', 'DEP-003', 'Emergency', 'Emergency', '2026-03-01', 320, 85, 82, 1.2, 0, 2, 0.0063, 12, 0.0375, 6400000.00, 20000.00),
('FAC-001', 'Apollo Main Hospital', 'DEP-004', 'Pediatrics', 'Inpatient', '2026-03-01', 110, 65, 63, 3.1, 72.0, 1, 0.0091, 5, 0.0455, 5500000.00, 50000.00),
('FAC-002', 'Apollo Cardiac Center', 'DEP-005', 'Neurology', 'Inpatient', '2026-03-01', 67, 55, 52, 5.8, 68.5, 2, 0.0299, 3, 0.0448, 8040000.00, 120000.00),
('FAC-002', 'Apollo Cardiac Center', 'DEP-006', 'Orthopedics', 'Inpatient', '2026-03-01', 95, 80, 78, 3.5, 75.0, 0, 0, 6, 0.0632, 7600000.00, 80000.00);

-- Population Health
INSERT INTO population_health (report_quarter, region, age_group, gender, disease_category, patient_count, encounter_count, avg_cost, avg_los, mortality_rate, complication_rate) VALUES
('2026-Q1', 'Chennai', '18-34', 'Male', 'Cardiovascular', 250, 380, 85000.00, 3.5, 0.008, 0.045),
('2026-Q1', 'Chennai', '35-54', 'Female', 'Oncology', 120, 290, 150000.00, 7.2, 0.042, 0.085),
('2026-Q1', 'Chennai', '55-74', 'Male', 'Neurological', 180, 310, 95000.00, 5.1, 0.022, 0.065),
('2026-Q1', 'Chennai', '0-17', 'Female', 'Respiratory', 340, 420, 35000.00, 2.8, 0.003, 0.025),
('2026-Q1', 'Chennai', '35-54', 'Male', 'Diabetes', 520, 680, 45000.00, 3.2, 0.015, 0.055),
('2026-Q1', 'Chennai', '75+', 'Female', 'Cardiovascular', 95, 210, 120000.00, 6.5, 0.068, 0.112);

-- Quality Metrics
INSERT INTO quality_metrics (facility_id, department_id, metric_name, metric_category, report_month, numerator, denominator, metric_value, target_value, benchmark_value, performance_status) VALUES
('FAC-001', 'DEP-001', 'Door-to-Balloon Time < 90 min', 'Timeliness', '2026-03-01', 42, 45, 93.33, 90.00, 95.00, 'Met'),
('FAC-001', 'DEP-001', 'Heart Failure Readmission Rate', 'Outcome', '2026-03-01', 8, 120, 6.67, 10.00, 8.50, 'Met'),
('FAC-001', 'DEP-002', 'Chemotherapy Completion Rate', 'Process', '2026-03-01', 62, 75, 82.67, 85.00, 80.00, 'Below Target'),
('FAC-001', 'DEP-003', 'ED Wait Time < 30 min', 'Timeliness', '2026-03-01', 245, 320, 76.56, 80.00, 75.00, 'Below Target'),
('FAC-001', 'DEP-004', 'Vaccination Compliance Rate', 'Process', '2026-03-01', 98, 110, 89.09, 90.00, 88.00, 'Met'),
('FAC-002', 'DEP-005', 'Stroke Response Time < 60 min', 'Timeliness', '2026-03-01', 48, 55, 87.27, 85.00, 82.00, 'Met');

-- Research Cohorts
INSERT INTO research_cohorts (study_name, pi_name, irb_number, start_date, end_date, status) VALUES
('Cardiac Biomarker Prediction Study', 'Dr. Patel', 'IRB-2025-001', '2025-06-01', '2027-06-01', 'active'),
('Pediatric Asthma Outcomes', 'Dr. Kumar', 'IRB-2025-012', '2025-09-01', '2027-03-01', 'active'),
('AI-Assisted Oncology Screening', 'Dr. Sharma', 'IRB-2026-003', '2026-01-15', '2028-01-15', 'enrolling');
