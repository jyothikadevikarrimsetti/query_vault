-- ============================================================
-- Sample Data for ApolloHIS and ApolloHR (MySQL)
-- ============================================================

USE ApolloHIS;

-- Facilities
INSERT INTO facilities (facility_name, facility_type, address, city, state, zip_code, phone) VALUES
('Apollo Main Hospital', 'Hospital', '123 Health Ave', 'Chennai', 'Tamil Nadu', '600001', '+91-44-2345-6789'),
('Apollo Cardiac Center', 'Specialty', '456 Heart Blvd', 'Chennai', 'Tamil Nadu', '600002', '+91-44-2345-6790'),
('Apollo Community Clinic', 'Clinic', '789 Care St', 'Chennai', 'Tamil Nadu', '600003', '+91-44-2345-6791');

-- Departments
INSERT INTO departments (department_name, facility_id, department_head, floor, wing) VALUES
('Cardiology', 1, 'Dr. Patel', '3', 'A'),
('Oncology', 1, 'Dr. Sharma', '4', 'B'),
('Emergency', 1, 'Dr. Reddy', '1', 'A'),
('Pediatrics', 1, 'Dr. Kumar', '2', 'C'),
('Neurology', 2, 'Dr. Singh', '2', 'A'),
('Orthopedics', 2, 'Dr. Gupta', '1', 'B'),
('General Medicine', 3, 'Dr. Iyer', '1', 'A');

-- Units
INSERT INTO units (unit_name, department_id, facility_id, bed_count, unit_type) VALUES
('ICU', 1, 1, 20, 'Intensive Care'),
('CCU', 1, 1, 15, 'Coronary Care'),
('General Ward A', 3, 1, 40, 'General'),
('Pediatric Ward', 4, 1, 25, 'Pediatric'),
('Oncology Ward', 2, 1, 30, 'Specialty'),
('Neuro ICU', 5, 2, 10, 'Intensive Care');

-- Patients
INSERT INTO patients (mrn, first_name, last_name, date_of_birth, gender, blood_type, phone, email, address, emergency_contact_name, emergency_contact_phone, insurance_id, aadhaar_number) VALUES
('MRN-001', 'Atharv', 'Menon', '1985-03-15', 'Male', 'O+', '+91-98765-43210', 'atharv.menon@email.com', '42 MG Road, Chennai', 'Priya Menon', '+91-98765-43211', 'INS-5001', '1234-5678-9012'),
('MRN-002', 'Sneha', 'Reddy', '1990-07-22', 'Female', 'A+', '+91-98765-43220', 'sneha.reddy@email.com', '15 Park Street, Chennai', 'Raj Reddy', '+91-98765-43221', 'INS-5002', '2345-6789-0123'),
('MRN-003', 'Vikram', 'Singh', '1978-11-08', 'Male', 'B+', '+91-98765-43230', 'vikram.singh@email.com', '88 Lake View, Chennai', 'Anjali Singh', '+91-98765-43231', 'INS-5003', '3456-7890-1234'),
('MRN-004', 'Priya', 'Nair', '1995-01-30', 'Female', 'AB-', '+91-98765-43240', 'priya.nair@email.com', '27 Temple Road, Chennai', 'Kumar Nair', '+91-98765-43241', 'INS-5004', '4567-8901-2345'),
('MRN-005', 'Rahul', 'Sharma', '1982-06-12', 'Male', 'A-', '+91-98765-43250', 'rahul.sharma@email.com', '63 Gandhi Nagar, Chennai', 'Meera Sharma', '+91-98765-43251', 'INS-5005', '5678-9012-3456'),
('MRN-006', 'Ananya', 'Iyer', '2000-09-05', 'Female', 'O-', '+91-98765-43260', 'ananya.iyer@email.com', '11 Beach Road, Chennai', 'Suresh Iyer', '+91-98765-43261', 'INS-5006', '6789-0123-4567'),
('MRN-007', 'Deepak', 'Gupta', '1970-12-20', 'Male', 'B-', '+91-98765-43270', 'deepak.gupta@email.com', '55 Anna Nagar, Chennai', 'Kavita Gupta', '+91-98765-43271', 'INS-5007', '7890-1234-5678'),
('MRN-008', 'Meera', 'Patel', '1988-04-18', 'Female', 'AB+', '+91-98765-43280', 'meera.patel@email.com', '99 T Nagar, Chennai', 'Amit Patel', '+91-98765-43281', 'INS-5008', '8901-2345-6789'),
('MRN-009', 'Arjun', 'Kumar', '1992-08-25', 'Male', 'O+', '+91-98765-43290', 'arjun.kumar@email.com', '33 Adyar, Chennai', 'Lakshmi Kumar', '+91-98765-43291', 'INS-5009', '9012-3456-7890'),
('MRN-010', 'Kavitha', 'Rajan', '1975-02-14', 'Female', 'A+', '+91-98765-43300', 'kavitha.rajan@email.com', '77 Mylapore, Chennai', 'Rajan V', '+91-98765-43301', 'INS-5010', '0123-4567-8901');

-- Encounters
INSERT INTO encounters (patient_id, encounter_type, admission_date, discharge_date, department_id, facility_id, attending_physician_id, diagnosis_code, diagnosis_description, status) VALUES
(1, 'Inpatient', '2026-03-01 08:00:00', '2026-03-05 14:00:00', 1, 1, 101, 'I25.1', 'Atherosclerotic heart disease', 'discharged'),
(2, 'Outpatient', '2026-03-10 09:00:00', '2026-03-10 11:00:00', 4, 1, 102, 'J06.9', 'Upper respiratory infection', 'completed'),
(3, 'Inpatient', '2026-03-15 10:00:00', NULL, 5, 2, 103, 'G40.9', 'Epilepsy, unspecified', 'active'),
(4, 'Emergency', '2026-03-20 02:30:00', '2026-03-20 08:00:00', 3, 1, 104, 'S52.5', 'Fracture of lower end of radius', 'discharged'),
(5, 'Inpatient', '2026-03-22 14:00:00', '2026-03-28 10:00:00', 2, 1, 105, 'C34.1', 'Malignant neoplasm of upper lobe, bronchus', 'discharged'),
(1, 'Outpatient', '2026-03-25 10:00:00', '2026-03-25 11:30:00', 1, 1, 101, 'I25.1', 'Follow-up cardiac evaluation', 'completed'),
(6, 'Inpatient', '2026-03-26 16:00:00', NULL, 1, 1, 101, 'I21.0', 'Acute myocardial infarction', 'active'),
(7, 'Outpatient', '2026-03-27 09:00:00', '2026-03-27 10:00:00', 7, 3, 106, 'E11.9', 'Type 2 diabetes mellitus', 'completed'),
(8, 'Inpatient', '2026-03-28 11:00:00', NULL, 4, 1, 102, 'A09.9', 'Gastroenteritis, unspecified', 'active'),
(9, 'Emergency', '2026-03-29 23:00:00', '2026-03-30 06:00:00', 3, 1, 104, 'T78.2', 'Anaphylactic shock', 'discharged');

-- Vital Signs
INSERT INTO vital_signs (patient_id, encounter_id, temperature, heart_rate, blood_pressure_systolic, blood_pressure_diastolic, respiratory_rate, oxygen_saturation, weight, height, recorded_by) VALUES
(1, 1, 98.6, 72, 130, 85, 16, 97.5, 75.0, 175.0, 'Nurse_Anil'),
(1, 1, 98.4, 70, 128, 82, 15, 98.0, 75.0, 175.0, 'Nurse_Anil'),
(2, 2, 99.1, 88, 118, 76, 18, 98.5, 62.0, 163.0, 'Nurse_Bala'),
(3, 3, 98.2, 65, 120, 78, 14, 99.0, 80.0, 180.0, 'Nurse_Chitra'),
(4, 4, 98.8, 95, 140, 90, 20, 96.5, 55.0, 160.0, 'Nurse_Divya'),
(5, 5, 99.5, 78, 135, 88, 19, 95.0, 68.0, 170.0, 'Nurse_Esha'),
(6, 7, 100.2, 110, 90, 60, 22, 94.0, 82.0, 172.0, 'Nurse_Anil'),
(7, 8, 98.4, 76, 145, 92, 16, 98.0, 90.0, 168.0, 'Nurse_Bala'),
(8, 9, 99.8, 92, 115, 72, 18, 97.0, 58.0, 155.0, 'Nurse_Chitra'),
(9, 10, 98.1, 105, 95, 55, 24, 93.0, 72.0, 178.0, 'Nurse_Divya');

-- Lab Results
INSERT INTO lab_results (patient_id, encounter_id, test_name, test_code, result_value, result_unit, reference_range, abnormal_flag, ordered_by, collected_at, resulted_at, status) VALUES
(1, 1, 'Troponin I', 'TROP', '0.15', 'ng/mL', '0.00-0.04', 'H', 'Dr. Patel', '2026-03-01 09:00:00', '2026-03-01 10:30:00', 'final'),
(1, 1, 'Complete Blood Count', 'CBC', '12.5', 'g/dL', '12.0-17.5', 'N', 'Dr. Patel', '2026-03-01 09:00:00', '2026-03-01 11:00:00', 'final'),
(3, 3, 'EEG', 'EEG001', 'Abnormal', NULL, NULL, 'A', 'Dr. Singh', '2026-03-15 12:00:00', '2026-03-15 15:00:00', 'final'),
(5, 5, 'CT Chest', 'CTCHST', 'Mass in upper lobe', NULL, NULL, 'A', 'Dr. Sharma', '2026-03-22 16:00:00', '2026-03-23 08:00:00', 'final'),
(5, 5, 'Biopsy', 'BIO01', 'Adenocarcinoma', NULL, NULL, 'A', 'Dr. Sharma', '2026-03-24 10:00:00', '2026-03-26 14:00:00', 'final'),
(6, 7, 'Troponin I', 'TROP', '2.85', 'ng/mL', '0.00-0.04', 'H', 'Dr. Patel', '2026-03-26 16:30:00', '2026-03-26 17:30:00', 'final'),
(7, 8, 'HbA1c', 'HBA1C', '8.2', '%', '4.0-5.6', 'H', 'Dr. Iyer', '2026-03-27 09:30:00', '2026-03-27 14:00:00', 'final'),
(9, 10, 'IgE', 'IGE', '450', 'IU/mL', '0-100', 'H', 'Dr. Reddy', '2026-03-29 23:30:00', '2026-03-30 02:00:00', 'final');

-- Prescriptions
INSERT INTO prescriptions (patient_id, encounter_id, medication_name, dosage, frequency, route, start_date, end_date, prescribed_by, status) VALUES
(1, 1, 'Aspirin', '81mg', 'Once daily', 'Oral', '2026-03-01', '2026-06-01', 'Dr. Patel', 'active'),
(1, 1, 'Atorvastatin', '40mg', 'Once daily', 'Oral', '2026-03-01', '2026-09-01', 'Dr. Patel', 'active'),
(5, 5, 'Cisplatin', '75mg/m2', 'Every 3 weeks', 'IV', '2026-03-25', '2026-06-25', 'Dr. Sharma', 'active'),
(6, 7, 'Heparin', '5000 units', 'Every 12 hours', 'Subcutaneous', '2026-03-26', '2026-03-31', 'Dr. Patel', 'active'),
(7, 8, 'Metformin', '500mg', 'Twice daily', 'Oral', '2026-03-27', '2026-09-27', 'Dr. Iyer', 'active'),
(9, 10, 'Epinephrine', '0.3mg', 'As needed', 'IM', '2026-03-29', '2026-03-30', 'Dr. Reddy', 'completed');

-- Allergies
INSERT INTO allergies (patient_id, allergen, reaction, severity, onset_date, reported_by, verified) VALUES
(1, 'Penicillin', 'Rash', 'Moderate', '2010-05-15', 'Dr. Patel', TRUE),
(4, 'Latex', 'Contact dermatitis', 'Mild', '2015-08-20', 'Dr. Kumar', TRUE),
(6, 'Shellfish', 'Anaphylaxis', 'Severe', '2018-01-10', 'Dr. Reddy', TRUE),
(9, 'Peanuts', 'Anaphylaxis', 'Severe', '2005-06-30', 'Dr. Reddy', TRUE),
(9, 'Tree nuts', 'Hives', 'Moderate', '2005-06-30', 'Dr. Reddy', TRUE),
(2, 'Sulfa drugs', 'Fever', 'Mild', '2020-03-12', 'Dr. Kumar', TRUE);

-- Appointments
INSERT INTO appointments (patient_id, provider_id, department_id, facility_id, appointment_date, appointment_time, duration_minutes, appointment_type, status) VALUES
(1, 101, 1, 1, '2026-04-05', '10:00:00', 30, 'Follow-up', 'scheduled'),
(2, 102, 4, 1, '2026-04-02', '14:00:00', 20, 'Check-up', 'scheduled'),
(5, 105, 2, 1, '2026-04-10', '09:00:00', 60, 'Chemotherapy', 'scheduled'),
(7, 106, 7, 3, '2026-04-15', '11:00:00', 30, 'Follow-up', 'scheduled'),
(8, 102, 4, 1, '2026-03-31', '09:00:00', 30, 'Follow-up', 'scheduled'),
(10, 106, 7, 3, '2026-03-31', '15:00:00', 30, 'Annual check-up', 'scheduled');

-- Clinical Notes
INSERT INTO clinical_notes (patient_id, encounter_id, note_type, author_id, note_text, is_signed, signed_by, signed_at) VALUES
(1, 1, 'Progress Note', 101, 'Patient admitted with chest pain. Troponin elevated. Started on anticoagulation therapy. Cardiac catheterization planned.', TRUE, 'Dr. Patel', '2026-03-01 20:00:00'),
(1, 1, 'Discharge Summary', 101, 'Patient recovered well post-catheterization. Stent placed in LAD. Discharge on dual antiplatelet therapy.', TRUE, 'Dr. Patel', '2026-03-05 12:00:00'),
(3, 3, 'Progress Note', 103, 'New onset seizures. EEG shows focal epileptiform activity. Started on levetiracetam 500mg BID.', TRUE, 'Dr. Singh', '2026-03-15 18:00:00'),
(5, 5, 'Progress Note', 105, 'CT-guided biopsy confirmed adenocarcinoma Stage IIIA. Discussed treatment plan with patient and family. Cisplatin-based chemotherapy to begin.', TRUE, 'Dr. Sharma', '2026-03-26 16:00:00'),
(6, 7, 'Progress Note', 101, 'Acute STEMI. Troponin markedly elevated. Emergency PCI performed. Drug-eluting stent placed in RCA.', TRUE, 'Dr. Patel', '2026-03-26 22:00:00');

-- Staff Schedules
INSERT INTO staff_schedules (employee_id, department_id, facility_id, shift_date, shift_start, shift_end, shift_type, is_on_call) VALUES
(1, 1, 1, '2026-03-31', '07:00:00', '15:00:00', 'Day', FALSE),
(2, 1, 1, '2026-03-31', '15:00:00', '23:00:00', 'Evening', FALSE),
(3, 3, 1, '2026-03-31', '23:00:00', '07:00:00', 'Night', TRUE),
(4, 4, 1, '2026-03-31', '07:00:00', '15:00:00', 'Day', FALSE);

-- ── ApolloHR Sample Data ────────────────────────────────────

USE ApolloHR;

INSERT INTO employees (first_name, last_name, email, phone, department_id, facility_id, job_title, hire_date, employment_status) VALUES
('Rajesh', 'Patel', 'rajesh.patel@apollo.com', '+91-98765-00001', 1, 1, 'Attending Physician', '2015-06-01', 'active'),
('Sunita', 'Sharma', 'sunita.sharma@apollo.com', '+91-98765-00002', 2, 1, 'Consulting Physician', '2018-03-15', 'active'),
('Arun', 'Reddy', 'arun.reddy@apollo.com', '+91-98765-00003', 3, 1, 'Emergency Physician', '2016-09-01', 'active'),
('Priya', 'Kumar', 'priya.kumar@apollo.com', '+91-98765-00004', 4, 1, 'Pediatrician', '2019-01-10', 'active'),
('Anil', 'Nair', 'anil.nair@apollo.com', '+91-98765-00005', 1, 1, 'Registered Nurse', '2017-04-20', 'active'),
('Bala', 'Subramaniam', 'bala.s@apollo.com', '+91-98765-00006', 4, 1, 'Registered Nurse', '2020-07-01', 'active'),
('Chitra', 'Devi', 'chitra.devi@apollo.com', '+91-98765-00007', 5, 2, 'Registered Nurse', '2019-11-15', 'active'),
('Divya', 'Rajan', 'divya.rajan@apollo.com', '+91-98765-00008', 3, 1, 'Emergency Nurse', '2018-06-01', 'active'),
('Manoj', 'Gupta', 'manoj.gupta@apollo.com', '+91-98765-00009', NULL, 1, 'Hospital Administrator', '2014-01-15', 'active'),
('Lakshmi', 'Venkat', 'lakshmi.v@apollo.com', '+91-98765-00010', NULL, 1, 'HR Director', '2016-03-01', 'active');

INSERT INTO payroll (employee_id, pay_period_start, pay_period_end, base_salary, overtime_pay, deductions, net_pay, payment_date, status) VALUES
(1, '2026-03-01', '2026-03-31', 250000.00, 0.00, 45000.00, 205000.00, '2026-03-31', 'processed'),
(2, '2026-03-01', '2026-03-31', 200000.00, 0.00, 38000.00, 162000.00, '2026-03-31', 'processed'),
(5, '2026-03-01', '2026-03-31', 80000.00, 12000.00, 15000.00, 77000.00, '2026-03-31', 'processed'),
(9, '2026-03-01', '2026-03-31', 180000.00, 0.00, 32000.00, 148000.00, '2026-03-31', 'processed'),
(10, '2026-03-01', '2026-03-31', 150000.00, 0.00, 28000.00, 122000.00, '2026-03-31', 'processed');

INSERT INTO leave_records (employee_id, leave_type, start_date, end_date, total_days, status, approved_by, reason) VALUES
(5, 'Sick Leave', '2026-03-10', '2026-03-11', 2, 'approved', 1, 'Fever'),
(6, 'Annual Leave', '2026-04-01', '2026-04-05', 5, 'approved', 4, 'Family vacation');

INSERT INTO certifications (employee_id, certification_name, issuing_body, issue_date, expiry_date, status) VALUES
(1, 'Board Certified Cardiologist', 'National Board of Examinations', '2015-01-01', '2027-01-01', 'active'),
(2, 'Board Certified Oncologist', 'National Board of Examinations', '2018-06-01', '2028-06-01', 'active'),
(5, 'Registered Nurse License', 'Indian Nursing Council', '2017-01-01', '2027-01-01', 'active');

INSERT INTO credentials (employee_id, credential_type, credential_number, issuing_authority, issue_date, expiry_date, verification_status, verified_at) VALUES
(1, 'Medical License', 'ML-TN-45210', 'Tamil Nadu Medical Council', '2015-06-01', '2027-06-01', 'verified', '2025-06-01 10:00:00'),
(2, 'Medical License', 'ML-TN-55102', 'Tamil Nadu Medical Council', '2018-03-15', '2028-03-15', 'verified', '2025-03-15 10:00:00');
