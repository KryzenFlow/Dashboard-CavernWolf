# BAA / HIPAA Compliance Checklist

Use this checklist when negotiating BAAs with CockroachDB Cloud, Azure, and SMS vendors.

## Core Data Siloing Rules

- Each clinic gets an independent CockroachDB logical schema: `clinic_{uniqueId}.patients`, `clinic_{uniqueId}.appointments`
- No SQL joins, views, or stored procedures across clinic schemas
- Hermes agent RBAC scoped to one clinic schema per session
- Production PHI tables store minimum necessary fields for booking and SMS only
- Medical notes, diagnosis, lab results never sent to SMS automation workflows
- Clawhub Docker sandbox uses synthetic/mock patient data only
- Production database dumps are encrypted, per-clinic separate archives

## Access & Audit Requirements

- All reads/writes to patient phone/appointment tables write immutable audit logs in the matching clinic schema
- Log fields: timestamp, Hermes agent ID, user/staff ID, action type, patient ID accessed, API source
- CockroachDB RBAC roles: `sms_automation`, `clinic_staff_limited`, `dba_audit`, `operator_backup`
- Azure Key Vault stores all secrets; no hardcoded credentials in repos

## Transmission & SMS Workflow Compliance

- SMS payloads contain zero PHI — only appointment time, clinic name, reschedule link
- Outbound SMS task queue is stateless; phone numbers purged after send
- TLS 1.3 for all traffic: Azure ↔ CockroachDB, Azure ↔ SMS provider, Hermes ↔ cloud database
- No patient data cached on frontend dashboards

## Git / Source Code IP & PHI Leak Prevention

- Production clinic schemas and audit SQL live in private repos only
- Public GitHub Pages demos use fully sanitized mock schemas
- Global `.gitignore` blocks database dumps, credential env files, raw production SQL

See also: `schemas/clinic_chiropractor_001.sql`, `docker-compose.sandbox.yml`
