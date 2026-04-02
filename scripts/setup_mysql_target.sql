-- ============================================================
-- ApolloHIS Database - Hospital Information System (MySQL)
-- ============================================================

CREATE DATABASE IF NOT EXISTS ApolloHIS;
CREATE DATABASE IF NOT EXISTS ApolloHR;

-- Grant permissions to sentinelsql user
GRANT ALL PRIVILEGES ON ApolloHIS.* TO 'sentinelsql'@'%';
GRANT ALL PRIVILEGES ON ApolloHR.* TO 'sentinelsql'@'%';
FLUSH PRIVILEGES;

-- ── ApolloHIS Tables ────────────────────────────────────────

USE ApolloHIS;

CREATE TABLE IF NOT EXISTS patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    mrn VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    blood_type VARCHAR(5),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    insurance_id VARCHAR(50),
    aadhaar_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS encounters (
    encounter_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    encounter_type VARCHAR(50),
    admission_date DATETIME,
    discharge_date DATETIME,
    department_id INT,
    facility_id INT,
    attending_physician_id INT,
    diagnosis_code VARCHAR(20),
    diagnosis_description TEXT,
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS vital_signs (
    vital_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    encounter_id INT,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    temperature DECIMAL(5,2),
    heart_rate INT,
    blood_pressure_systolic INT,
    blood_pressure_diastolic INT,
    respiratory_rate INT,
    oxygen_saturation DECIMAL(5,2),
    weight DECIMAL(6,2),
    height DECIMAL(5,2),
    recorded_by VARCHAR(100),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS lab_results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    encounter_id INT,
    test_name VARCHAR(100),
    test_code VARCHAR(20),
    result_value VARCHAR(100),
    result_unit VARCHAR(30),
    reference_range VARCHAR(50),
    abnormal_flag VARCHAR(10),
    ordered_by VARCHAR(100),
    collected_at DATETIME,
    resulted_at DATETIME,
    status VARCHAR(30) DEFAULT 'final',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    encounter_id INT,
    medication_name VARCHAR(200),
    dosage VARCHAR(50),
    frequency VARCHAR(50),
    route VARCHAR(30),
    start_date DATE,
    end_date DATE,
    prescribed_by VARCHAR(100),
    pharmacy_notes TEXT,
    status VARCHAR(30) DEFAULT 'active',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS allergies (
    allergy_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    allergen VARCHAR(100),
    reaction VARCHAR(200),
    severity VARCHAR(20),
    onset_date DATE,
    reported_by VARCHAR(100),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    facility_id INT,
    department_head VARCHAR(100),
    floor VARCHAR(10),
    wing VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS facilities (
    facility_id INT AUTO_INCREMENT PRIMARY KEY,
    facility_name VARCHAR(200) NOT NULL,
    facility_type VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    provider_id INT,
    department_id INT,
    facility_id INT,
    appointment_date DATE,
    appointment_time TIME,
    duration_minutes INT DEFAULT 30,
    appointment_type VARCHAR(50),
    status VARCHAR(30) DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS clinical_notes (
    note_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    encounter_id INT,
    note_type VARCHAR(50),
    author_id INT,
    note_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_signed BOOLEAN DEFAULT FALSE,
    signed_by VARCHAR(100),
    signed_at DATETIME,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS staff_schedules (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    department_id INT,
    facility_id INT,
    shift_date DATE,
    shift_start TIME,
    shift_end TIME,
    shift_type VARCHAR(20),
    is_on_call BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS units (
    unit_id INT AUTO_INCREMENT PRIMARY KEY,
    unit_name VARCHAR(100) NOT NULL,
    department_id INT,
    facility_id INT,
    bed_count INT DEFAULT 0,
    unit_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── ApolloHR Tables ─────────────────────────────────────────

USE ApolloHR;

CREATE TABLE IF NOT EXISTS employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    department_id INT,
    facility_id INT,
    job_title VARCHAR(100),
    hire_date DATE,
    employment_status VARCHAR(30) DEFAULT 'active',
    manager_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payroll (
    payroll_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    pay_period_start DATE,
    pay_period_end DATE,
    base_salary DECIMAL(12,2),
    overtime_pay DECIMAL(10,2) DEFAULT 0,
    deductions DECIMAL(10,2) DEFAULT 0,
    net_pay DECIMAL(12,2),
    bank_account VARCHAR(50),
    payment_date DATE,
    status VARCHAR(30) DEFAULT 'processed',
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS leave_records (
    leave_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    leave_type VARCHAR(30),
    start_date DATE,
    end_date DATE,
    total_days DECIMAL(4,1),
    status VARCHAR(30) DEFAULT 'pending',
    approved_by INT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS certifications (
    cert_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    certification_name VARCHAR(200),
    issuing_body VARCHAR(200),
    issue_date DATE,
    expiry_date DATE,
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS credentials (
    credential_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    credential_type VARCHAR(50),
    credential_number VARCHAR(50),
    issuing_authority VARCHAR(200),
    issue_date DATE,
    expiry_date DATE,
    verification_status VARCHAR(30) DEFAULT 'pending',
    verified_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);
