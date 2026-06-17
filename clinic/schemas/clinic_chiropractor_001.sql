-- Isolated clinic schema for SMS/appointment workflows (mock/production template)
-- Repeat CREATE SCHEMA for each new clinic client.

CREATE SCHEMA IF NOT EXISTS clinic_chiropractor_001;

CREATE ROLE IF NOT EXISTS sms_automation;
GRANT USAGE ON SCHEMA clinic_chiropractor_001 TO sms_automation;

CREATE TABLE IF NOT EXISTS clinic_chiropractor_001.patients (
    patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name STRING NOT NULL,
    cell_phone STRING NOT NULL,
    email STRING,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS clinic_chiropractor_001.patient_medical_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES clinic_chiropractor_001.patients(patient_id),
    diagnosis STRING,
    treatment_notes STRING,
    visit_cost DECIMAL,
    record_created TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS clinic_chiropractor_001.appointments (
    appointment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES clinic_chiropractor_001.patients(patient_id),
    provider_name STRING NOT NULL,
    appointment_start TIMESTAMPTZ NOT NULL,
    appointment_end TIMESTAMPTZ NOT NULL,
    status STRING DEFAULT 'scheduled',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS clinic_chiropractor_001.data_access_audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_role STRING NOT NULL,
    agent_source STRING NOT NULL,
    patient_id UUID,
    action_type STRING NOT NULL,
    accessed_columns STRING[],
    access_timestamp TIMESTAMPTZ DEFAULT NOW()
);

GRANT SELECT (patient_id, full_name, cell_phone) ON clinic_chiropractor_001.patients TO sms_automation;
GRANT SELECT ON clinic_chiropractor_001.appointments TO sms_automation;
REVOKE ALL ON clinic_chiropractor_001.patient_medical_records FROM sms_automation;
