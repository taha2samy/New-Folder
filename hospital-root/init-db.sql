CREATE DATABASE patient_db;
CREATE DATABASE clinical_db;
CREATE DATABASE pharmacy_db;
CREATE DATABASE aggregator_db;
CREATE DATABASE laboratory_db;
CREATE DATABASE reference_db;
CREATE DATABASE keycloak_db;

\c reference_db;

-- Base Tables (UUIDs hardcoded for deterministic seeding)
CREATE TABLE IF NOT EXISTS disease_types (
    id VARCHAR PRIMARY KEY,
    code VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS diseases (
    id VARCHAR PRIMARY KEY,
    code VARCHAR UNIQUE NOT NULL,
    description TEXT NOT NULL,
    disease_type_id VARCHAR REFERENCES disease_types(id) NOT NULL,
    created_by VARCHAR,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS wards (
    id VARCHAR PRIMARY KEY,
    code VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    beds_count INTEGER NOT NULL,
    is_opd BOOLEAN NOT NULL,
    created_by VARCHAR,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS exam_types (
    id VARCHAR PRIMARY KEY,
    code VARCHAR UNIQUE NOT NULL,
    description TEXT NOT NULL,
    procedure_type VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS operation_types (
    id VARCHAR PRIMARY KEY,
    code VARCHAR UNIQUE NOT NULL,
    description TEXT NOT NULL,
    is_major BOOLEAN NOT NULL
);

-- Seed Disease Types
INSERT INTO disease_types (id, code, name) VALUES
('type-inf-001', 'INF', 'Infectious and Parasitic Diseases'),
('type-chr-001', 'CHR', 'Chronic Diseases')
ON CONFLICT (code) DO NOTHING;

-- Seed Diseases
INSERT INTO diseases (id, code, description, disease_type_id) VALUES
('dis-001', 'A00', 'Cholera', 'type-inf-001'),
('dis-002', 'B01', 'Varicella (Chickenpox)', 'type-inf-001'),
('dis-003', 'E11', 'Type 2 Diabetes Mellitus', 'type-chr-001'),
('dis-004', 'I10', 'Essential (primary) hypertension', 'type-chr-001')
ON CONFLICT (code) DO NOTHING;

-- Seed Wards
INSERT INTO wards (id, code, name, beds_count, is_opd) VALUES
('ward-mat-01', 'MAT', 'Maternity Ward', 40, false),
('ward-opd-01', 'OPD', 'Outpatient Department', 0, true),
('ward-icu-01', 'ICU', 'Intensive Care Unit', 15, false),
('ward-gen-01', 'GEN', 'General Ward', 100, false)
ON CONFLICT (code) DO NOTHING;

-- Seed Exam Types
INSERT INTO exam_types (id, code, description, procedure_type) VALUES
('exam-001', 'CBC', 'Complete Blood Count', 'SINGLE_VALUE'),
('exam-002', 'LIPID', 'Lipid Panel', 'MULTIPLE_BOOLEAN'),
('exam-003', 'URINE', 'Urinalysis', 'SINGLE_VALUE'),
('exam-004', 'XRAY-CHEST', 'Chest X-Ray', 'MANUAL_TEXT')
ON CONFLICT (code) DO NOTHING;

-- Seed Operation Types
INSERT INTO operation_types (id, code, description, is_major) VALUES
('op-001', 'APPEN', 'Appendectomy', true),
('op-002', 'CESAR', 'Cesarean Section', true),
('op-003', 'SUT', 'Suturing of minor lacerations', false)
ON CONFLICT (code) DO NOTHING;
