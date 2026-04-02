-- ============================================================
-- Sample Data for apollo_financial (PostgreSQL)
-- ============================================================

-- Insurance Plans
INSERT INTO insurance_plans (plan_name, payer_name, plan_type, coverage_start, coverage_end, premium, deductible, copay, is_active) VALUES
('Apollo Gold', 'Star Health', 'PPO', '2026-01-01', '2026-12-31', 15000.00, 5000.00, 500.00, TRUE),
('Apollo Silver', 'ICICI Lombard', 'HMO', '2026-01-01', '2026-12-31', 10000.00, 10000.00, 750.00, TRUE),
('Apollo Platinum', 'Max Bupa', 'PPO', '2026-01-01', '2026-12-31', 25000.00, 2000.00, 250.00, TRUE),
('Government CGHS', 'CGHS', 'Government', '2025-04-01', '2026-03-31', 0.00, 0.00, 0.00, TRUE);

-- Claims
INSERT INTO claims (patient_id, encounter_id, claim_type, total_amount, insurance_id, facility_id, submitted_date, adjudicated_date, status) VALUES
(1, 1, 'Inpatient', 450000.00, 'INS-5001', 'FAC-001', '2026-03-06', '2026-03-15', 'paid'),
(2, 2, 'Outpatient', 5000.00, 'INS-5002', 'FAC-001', '2026-03-11', '2026-03-18', 'paid'),
(5, 5, 'Inpatient', 850000.00, 'INS-5005', 'FAC-001', '2026-03-29', NULL, 'submitted'),
(6, 7, 'Inpatient', 650000.00, 'INS-5006', 'FAC-001', '2026-03-27', NULL, 'submitted'),
(4, 4, 'Emergency', 75000.00, 'INS-5004', 'FAC-001', '2026-03-21', '2026-03-28', 'paid');

-- Claim Line Items
INSERT INTO claim_line_items (claim_id, procedure_code, description, quantity, unit_price, total_price, service_date) VALUES
(1, '93458', 'Cardiac catheterization', 1, 200000.00, 200000.00, '2026-03-02'),
(1, '92928', 'Coronary stent placement', 1, 150000.00, 150000.00, '2026-03-03'),
(1, '99223', 'Hospital care, high severity', 5, 20000.00, 100000.00, '2026-03-01'),
(3, '96413', 'Chemotherapy administration', 1, 350000.00, 350000.00, '2026-03-25'),
(5, '99281', 'Emergency department visit', 1, 25000.00, 25000.00, '2026-03-20');

-- Patient Billing
INSERT INTO patient_billing (patient_id, encounter_id, total_charges, insurance_paid, patient_responsibility, payment_status, due_date) VALUES
(1, 1, 450000.00, 360000.00, 90000.00, 'partial', '2026-04-30'),
(2, 2, 5000.00, 4000.00, 1000.00, 'paid', '2026-04-15'),
(4, 4, 75000.00, 60000.00, 15000.00, 'paid', '2026-04-20'),
(5, 5, 850000.00, 0.00, 850000.00, 'pending', '2026-05-15');

-- Payer Contracts
INSERT INTO payer_contracts (payer_name, contract_type, effective_date, termination_date, reimbursement_rate, fee_schedule, status) VALUES
('Star Health', 'PPO', '2025-01-01', '2027-12-31', 0.80, 'Standard fee schedule 2025', 'active'),
('ICICI Lombard', 'HMO', '2025-06-01', '2027-05-31', 0.75, 'Capitation model', 'active'),
('Max Bupa', 'PPO', '2026-01-01', '2027-12-31', 0.85, 'Premium fee schedule', 'active');

-- Payments
INSERT INTO payments (claim_id, patient_id, amount, payment_method, payment_date, reference_number, payer_type, status) VALUES
(1, 1, 360000.00, 'Insurance', '2026-03-20', 'PAY-2026-001', 'Insurance', 'processed'),
(1, 1, 50000.00, 'Credit Card', '2026-03-25', 'PAY-2026-002', 'Patient', 'processed'),
(2, 2, 4000.00, 'Insurance', '2026-03-22', 'PAY-2026-003', 'Insurance', 'processed'),
(2, 2, 1000.00, 'UPI', '2026-03-23', 'PAY-2026-004', 'Patient', 'processed'),
(5, 4, 60000.00, 'Insurance', '2026-03-30', 'PAY-2026-005', 'Insurance', 'processed');
