"""Seed Neo4j with roles, users, tables, columns, and default policies.

All operations use MERGE for idempotency -- safe to re-run.
Reads role hierarchy, clearance, domain, and policy data from role_resolver.py.
Discovers real columns from PostgreSQL information_schema.

Usage:
    python -m queryvault.scripts.seed_neo4j
"""

from __future__ import annotations

import asyncio
import os
import sys

# ---------------------------------------------------------------------------
# Data sources (imported from existing hardcoded dicts)
# ---------------------------------------------------------------------------

from queryvault.app.services.identity.role_resolver import (
    ROLE_CLEARANCE,
    ROLE_DOMAIN,
    ROLE_INHERITANCE,
    ROLE_POLICIES,
)
from queryvault.app.api.user_directory_routes import USER_PROFILES
from queryvault.app.models.enums import ClearanceLevel, Domain

# ---------------------------------------------------------------------------
# Table definitions — all databases
# ---------------------------------------------------------------------------

TABLE_DEFINITIONS = {
    # ── apollo_analytics (PostgreSQL) ──────────────────────────
    "encounter_summaries": {"sensitivity_level": 3, "domain": "CLINICAL"},
    "population_health":   {"sensitivity_level": 2, "domain": "CLINICAL"},
    "quality_metrics":     {"sensitivity_level": 2, "domain": "ADMINISTRATIVE"},
    "research_cohorts":    {"sensitivity_level": 3, "domain": "RESEARCH"},

    # ── ApolloHIS (MySQL) — Hospital Information System ────────
    "patients":            {"sensitivity_level": 4, "domain": "HIS"},
    "encounters":          {"sensitivity_level": 3, "domain": "HIS"},
    "vital_signs":         {"sensitivity_level": 3, "domain": "HIS"},
    "lab_results":         {"sensitivity_level": 3, "domain": "HIS"},
    "prescriptions":       {"sensitivity_level": 3, "domain": "HIS"},
    "allergies":           {"sensitivity_level": 3, "domain": "HIS"},
    "appointments":        {"sensitivity_level": 2, "domain": "HIS"},
    "clinical_notes":      {"sensitivity_level": 4, "domain": "HIS"},
    "departments":         {"sensitivity_level": 1, "domain": "HIS"},
    "facilities":          {"sensitivity_level": 1, "domain": "HIS"},
    "staff_schedules":     {"sensitivity_level": 2, "domain": "HIS"},
    "units":               {"sensitivity_level": 1, "domain": "HIS"},

    # ── ApolloHR (MySQL) — Human Resources ─────────────────────
    "employees":           {"sensitivity_level": 3, "domain": "HR"},
    "payroll":             {"sensitivity_level": 5, "domain": "HR"},
    "leave_records":       {"sensitivity_level": 2, "domain": "HR"},
    "certifications":      {"sensitivity_level": 2, "domain": "HR"},
    "credentials":         {"sensitivity_level": 3, "domain": "HR"},

    # ── apollo_financial (PostgreSQL) ──────────────────────────
    "claims":              {"sensitivity_level": 3, "domain": "FINANCIAL"},
    "claim_line_items":    {"sensitivity_level": 2, "domain": "FINANCIAL"},
    "insurance_plans":     {"sensitivity_level": 2, "domain": "FINANCIAL"},
    "patient_billing":     {"sensitivity_level": 3, "domain": "FINANCIAL"},
    "payer_contracts":     {"sensitivity_level": 3, "domain": "FINANCIAL"},
    "payments":            {"sensitivity_level": 3, "domain": "FINANCIAL"},
}

# ---------------------------------------------------------------------------
# Default role -> table access policies
# ---------------------------------------------------------------------------

ROLE_TABLE_ACCESS: dict[str, dict] = {
    # ── Clinical roles ─────────────────────────────────────────
    "ATTENDING_PHYSICIAN":   {
        "allow": [
            "encounter_summaries", "population_health", "quality_metrics",
            "patients", "encounters", "vital_signs", "lab_results",
            "prescriptions", "allergies", "appointments", "clinical_notes",
            "departments", "facilities", "units",
        ],
        "deny": [],
    },
    "CONSULTING_PHYSICIAN":  {
        "allow": [
            "encounter_summaries", "population_health",
            "patients", "encounters", "vital_signs", "lab_results",
            "prescriptions", "allergies", "appointments", "clinical_notes",
        ],
        "deny": [],
    },
    "EMERGENCY_PHYSICIAN":   {
        "allow": [
            "encounter_summaries", "population_health", "quality_metrics",
            "patients", "encounters", "vital_signs", "lab_results",
            "prescriptions", "allergies", "appointments", "clinical_notes",
            "departments", "facilities", "units",
        ],
        "deny": [],
    },
    "PSYCHIATRIST":          {
        "allow": [
            "encounter_summaries", "population_health",
            "patients", "encounters", "clinical_notes", "prescriptions",
        ],
        "deny": [],
    },
    "RESIDENT":              {
        "allow": [
            "encounter_summaries", "population_health",
            "patients", "encounters", "vital_signs", "lab_results",
            "prescriptions", "allergies", "appointments",
        ],
        "deny": ["research_cohorts"],
    },
    "HEAD_NURSE":            {
        "allow": [
            "encounter_summaries", "population_health",
            "patients", "encounters", "vital_signs", "allergies",
            "appointments", "staff_schedules", "departments", "units",
        ],
        "deny": ["research_cohorts"],
    },
    "ICU_NURSE":             {
        "allow": [
            "encounter_summaries", "population_health",
            "patients", "encounters", "vital_signs", "lab_results",
            "allergies", "prescriptions",
        ],
        "deny": ["research_cohorts"],
    },
    "REGISTERED_NURSE":      {
        "allow": [
            "encounter_summaries", "population_health",
            "patients", "encounters", "vital_signs", "allergies",
            "appointments",
        ],
        "deny": ["research_cohorts"],
    },

    # ── Financial roles ────────────────────────────────────────
    "BILLING_CLERK":         {
        "allow": [
            "quality_metrics", "population_health",
            "claims", "claim_line_items", "insurance_plans", "payments",
        ],
        "deny": ["encounter_summaries"],
    },
    "REVENUE_CYCLE_ANALYST": {
        "allow": [
            "quality_metrics", "population_health",
            "claims", "claim_line_items", "payer_contracts", "payments",
        ],
        "deny": ["encounter_summaries"],
    },
    "REVENUE_CYCLE_MANAGER": {
        "allow": [
            "quality_metrics", "population_health",
            "claims", "claim_line_items", "insurance_plans",
            "payer_contracts", "payments", "patient_billing",
        ],
        "deny": ["encounter_summaries"],
    },

    # ── HR roles ───────────────────────────────────────────────
    "HR_MANAGER":            {
        "allow": [
            "quality_metrics",
            "employees", "leave_records", "certifications", "credentials",
        ],
        "deny": ["encounter_summaries", "research_cohorts", "payroll"],
    },
    "HR_DIRECTOR":           {
        "allow": [
            "quality_metrics", "population_health",
            "employees", "payroll", "leave_records", "certifications", "credentials",
        ],
        "deny": [],
    },

    # ── IT ─────────────────────────────────────────────────────
    "IT_ADMINISTRATOR":      {
        "allow": ["quality_metrics"],
        "deny": [],
    },

    # ── Compliance — full access for auditing ──────────────────
    "HIPAA_PRIVACY_OFFICER": {
        "allow": [
            "encounter_summaries", "population_health", "quality_metrics", "research_cohorts",
            "patients", "encounters", "vital_signs", "lab_results",
            "prescriptions", "allergies", "appointments", "clinical_notes",
            "employees", "credentials",
            "claims", "insurance_plans", "patient_billing",
        ],
        "deny": [],
    },

    # ── Research ───────────────────────────────────────────────
    "CLINICAL_RESEARCHER":   {
        "allow": ["research_cohorts", "population_health"],
        "deny": ["encounter_summaries"],
    },
}

# All non-admin roles denied these operations
DENIED_OPS_FOR_ALL = ["DELETE", "DROP", "ALTER", "TRUNCATE"]

# Row filters by role
ROLE_ROW_FILTERS: dict[str, list[dict]] = {
    "REGISTERED_NURSE": [
        {"table": "encounter_summaries", "condition": "facility_id = '{{user.facility}}'"},
        {"table": "patients", "condition": "facility_id = '{{user.facility}}'"},
        {"table": "encounters", "condition": "facility_id = '{{user.facility}}'"},
    ],
    "BILLING_CLERK": [
        {"table": "quality_metrics", "condition": "facility_id = '{{user.facility}}'"},
        {"table": "claims", "condition": "facility_id = '{{user.facility}}'"},
    ],
    "RESIDENT": [
        {"table": "encounter_summaries", "condition": "department_name = '{{user.department}}'"},
        {"table": "patients", "condition": "department_id = '{{user.department}}'"},
    ],
    "HR_MANAGER": [
        {"table": "employees", "condition": "department_id = '{{user.department}}'"},
    ],
}

# PII-like column name patterns -> higher classification
PII_PATTERNS = {"patient", "name", "ssn", "dob", "mrn", "aadhaar", "phone", "email", "address", "npi", "salary", "bank", "iban"}

# Per-role column visibility overrides
# Format: {role: {table: {column: visibility}}}
ROLE_COLUMN_POLICIES: dict[str, dict[str, dict[str, str]]] = {
    "REGISTERED_NURSE": {
        "patients": {
            "first_name": "MASKED",
            "last_name": "MASKED",
            "full_name": "MASKED",
            "aadhaar_number": "HIDDEN",
            "date_of_birth": "HIDDEN",
            "email": "HIDDEN",
            "phone_primary": "HIDDEN",
            "phone_secondary": "HIDDEN",
            "address_line1": "HIDDEN",
            "address_line2": "HIDDEN",
            "emergency_contact_phone": "HIDDEN",
        },
        "encounters": {
            "primary_dx_desc": "MASKED",
        },
    },
    "ICU_NURSE": {
        "patients": {
            "first_name": "MASKED",
            "last_name": "MASKED",
            "full_name": "MASKED",
            "aadhaar_number": "HIDDEN",
            "email": "HIDDEN",
            "phone_primary": "HIDDEN",
            "phone_secondary": "HIDDEN",
            "address_line1": "HIDDEN",
            "address_line2": "HIDDEN",
        },
    },
    "HEAD_NURSE": {
        "patients": {
            "first_name": "MASKED",
            "last_name": "MASKED",
            "full_name": "MASKED",
            "aadhaar_number": "HIDDEN",
            "email": "HIDDEN",
            "address_line1": "HIDDEN",
            "address_line2": "HIDDEN",
        },
    },
    "BILLING_CLERK": {
        "claims": {
            "patient_id": "MASKED",
        },
        "payments": {
            "reference_number": "MASKED",
        },
    },
    "HR_MANAGER": {
        "employees": {
            "email": "MASKED",
            "phone": "MASKED",
        },
    },
    "CONSULTING_PHYSICIAN": {
        "patients": {
            "aadhaar_number": "HIDDEN",
            "address_line1": "HIDDEN",
            "address_line2": "HIDDEN",
        },
    },
    "CLINICAL_RESEARCHER": {
        "population_health": {
            "patient_count": "VISIBLE",
        },
    },
}

OPERATIONS = ["DELETE", "UPDATE", "DROP", "ALTER", "TRUNCATE"]
DOMAINS = ["CLINICAL", "FINANCIAL", "ADMINISTRATIVE", "RESEARCH", "COMPLIANCE", "IT_OPERATIONS", "HIS", "HR"]


async def seed_all(neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                   neo4j_database: str = "neo4j", pg_dsn: str | None = None) -> dict:
    """Run the full seed pipeline. Returns summary stats."""
    from neo4j import AsyncGraphDatabase

    driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    await driver.verify_connectivity()
    print(f"Connected to Neo4j at {neo4j_uri}")

    stats: dict[str, int] = {}

    async with driver.session(database=neo4j_database) as session:
        # 1. Constraints
        await _create_constraints(session)
        print("  [1/8] Constraints created")

        # 2. Domains
        stats["domains"] = await _seed_domains(session)
        print(f"  [2/8] Domains: {stats['domains']}")

        # 3. Operations
        stats["operations"] = await _seed_operations(session)
        print(f"  [3/8] Operations: {stats['operations']}")

        # 4. Roles + ACCESS_DOMAIN edges
        stats["roles"] = await _seed_roles(session)
        print(f"  [4/8] Roles: {stats['roles']}")

        # 5. Tables + IN_DOMAIN edges
        stats["tables"] = await _seed_tables(session)
        print(f"  [5/8] Tables: {stats['tables']}")

        # 6. Columns (from PostgreSQL + fallback for MySQL tables)
        stats["columns"] = await _seed_columns(session, pg_dsn)
        print(f"  [6/8] Columns: {stats['columns']}")

        # 7. Users + HAS_ROLE edges
        stats["users"] = await _seed_users(session)
        print(f"  [7/8] Users: {stats['users']}")

        # 8. Policy edges (ALLOWS_TABLE, DENIES_TABLE, DENIES_OP, ROW_FILTER)
        stats["policy_edges"] = await _seed_policy_edges(session)
        print(f"  [8/9] Policy edges: {stats['policy_edges']}")

        # 9. Role column policies (COLUMN_POLICY edges)
        stats["column_policies"] = await _seed_role_column_policies(session)
        print(f"  [9/9] Column policies: {stats['column_policies']}")

    await driver.close()
    print(f"\nSeed complete: {stats}")
    return stats


async def _create_constraints(session) -> None:
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Table) REQUIRE t.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Operation) REQUIRE o.name IS UNIQUE",
    ]
    for c in constraints:
        try:
            await session.run(c)
        except Exception as exc:
            # If a plain index already exists on this property, drop it first and retry
            err_msg = str(exc)
            if "already exists an index" in err_msg:
                # Extract label from constraint (e.g. "Table" from "FOR (t:Table)")
                label = c.split(":")[1].split(")")[0]
                prop = c.split(".")[-1].split(" ")[0]
                drop_idx = f"DROP INDEX ON :{label}({prop})"
                try:
                    await session.run(drop_idx)
                    await session.run(c)
                    print(f"    Dropped conflicting index on :{label}({prop}), constraint created")
                except Exception:
                    print(f"    Warning: could not resolve index conflict for {label}.{prop}, skipping constraint")
            else:
                print(f"    Warning: constraint skipped -- {err_msg}")


async def _seed_domains(session) -> int:
    for d in DOMAINS:
        await session.run("MERGE (d:Domain {name: $name})", name=d)
    return len(DOMAINS)


async def _seed_operations(session) -> int:
    for op in OPERATIONS:
        await session.run("MERGE (o:Operation {name: $name})", name=op)
    return len(OPERATIONS)


async def _seed_roles(session) -> int:
    count = 0
    all_roles = set(ROLE_INHERITANCE.keys())
    # Also add parent roles that aren't keys
    for parents in ROLE_INHERITANCE.values():
        all_roles.update(parents)

    for role_name in sorted(all_roles):
        clearance = ROLE_CLEARANCE.get(role_name, ClearanceLevel.PUBLIC).value
        domain_enum = ROLE_DOMAIN.get(role_name)
        domain = domain_enum.value if domain_enum else ""
        policies = ROLE_POLICIES.get(role_name, [])

        await session.run(
            """
            MERGE (r:Role {name: $name})
            SET r.clearance_level = $clearance,
                r.domain = $domain,
                r.bound_policies = $policies
            """,
            name=role_name, clearance=clearance, domain=domain, policies=policies,
        )

        # ACCESS_DOMAIN edge
        if domain:
            await session.run(
                """
                MATCH (r:Role {name: $role}), (d:Domain {name: $domain})
                MERGE (r)-[:ACCESS_DOMAIN]->(d)
                """,
                role=role_name, domain=domain,
            )

        # Clinical roles also get HIS domain access
        if domain == "CLINICAL":
            await session.run(
                """
                MATCH (r:Role {name: $role}), (d:Domain {name: 'HIS'})
                MERGE (r)-[:ACCESS_DOMAIN]->(d)
                """,
                role=role_name,
            )

        count += 1

    return count


async def _seed_tables(session) -> int:
    for table_name, meta in TABLE_DEFINITIONS.items():
        await session.run(
            """
            MERGE (t:Table {name: $name})
            SET t.sensitivity_level = $sensitivity, t.domain = $domain
            """,
            name=table_name,
            sensitivity=meta["sensitivity_level"],
            domain=meta["domain"],
        )
        # IN_DOMAIN edge
        await session.run(
            """
            MATCH (t:Table {name: $table}), (d:Domain {name: $domain})
            MERGE (t)-[:IN_DOMAIN]->(d)
            """,
            table=table_name, domain=meta["domain"],
        )
    return len(TABLE_DEFINITIONS)


async def _seed_columns(session, pg_dsn: str | None) -> int:
    """Discover columns from PostgreSQL and seed into Neo4j."""
    count = 0

    # Try live PG discovery for analytics/financial tables
    if pg_dsn:
        try:
            import asyncpg
            conn = await asyncpg.connect(pg_dsn)
            rows = await conn.fetch(
                """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name IN ('encounter_summaries', 'population_health', 'quality_metrics', 'research_cohorts')
                ORDER BY table_name, ordinal_position
                """
            )
            await conn.close()

            for row in rows:
                count += await _upsert_column(session, row["table_name"], row["column_name"], row["data_type"])

            print(f"    (PG live discovery: {count} columns)")
        except Exception as exc:
            print(f"    (PG connection failed: {exc} -- using fallback)")
            count += await _seed_columns_fallback(session)
    else:
        print("    (No PG DSN -- using fallback column list)")
        count += await _seed_columns_fallback(session)

    # Always seed HIS/HR/Financial fallback columns (MySQL tables + financial)
    count += await _seed_columns_his_hr_financial(session)

    return count


async def _upsert_column(session, table_name: str, col_name: str, data_type: str = "unknown") -> int:
    """Create or update a single column node with PII heuristics."""
    is_pii = any(p in col_name.lower() for p in PII_PATTERNS)
    classification = 3 if is_pii else 1
    visibility = "MASKED" if is_pii else "VISIBLE"

    await session.run(
        """
        MERGE (c:Column {name: $col_name, table: $table_name})
        SET c.data_type = $data_type,
            c.classification_level = $classification,
            c.default_visibility = $visibility,
            c.is_pii = $is_pii
        """,
        col_name=col_name, table_name=table_name,
        data_type=data_type, classification=classification,
        visibility=visibility, is_pii=is_pii,
    )
    await session.run(
        """
        MATCH (c:Column {name: $col, table: $table}), (t:Table {name: $table})
        MERGE (c)-[:BELONGS_TO]->(t)
        """,
        col=col_name, table=table_name,
    )
    return 1


async def _seed_columns_fallback(session) -> int:
    """Fallback column list for analytics tables when PostgreSQL isn't reachable."""
    FALLBACK_COLUMNS = {
        "encounter_summaries": [
            "summary_id", "facility_id", "facility_name", "department_id", "department_name",
            "report_month", "encounter_type", "total_encounters", "total_admissions",
            "total_discharges", "avg_length_of_stay", "readmission_count", "readmission_rate",
            "total_revenue", "avg_revenue_per_encounter", "bed_occupancy_rate",
            "mortality_count", "mortality_rate", "created_at",
        ],
        "population_health": [
            "record_id", "facility_id", "report_quarter", "age_group", "gender",
            "disease_category", "icd_chapter", "patient_count", "encounter_count",
            "avg_cost", "avg_los", "complication_rate", "created_at",
        ],
        "quality_metrics": [
            "metric_id", "facility_id", "department_id", "metric_name", "metric_category",
            "report_month", "numerator", "denominator", "metric_value",
            "target_value", "benchmark_value", "performance_status", "created_at",
        ],
        "research_cohorts": [
            "cohort_id", "cohort_name", "study_id", "principal_investigator",
            "department_id", "inclusion_criteria", "exclusion_criteria",
            "patient_count", "enrollment_start", "enrollment_end",
            "status", "irb_approval_number", "created_at",
        ],
    }
    count = 0
    for table_name, columns in FALLBACK_COLUMNS.items():
        for col_name in columns:
            count += await _upsert_column(session, table_name, col_name)
    return count


async def _seed_columns_his_hr_financial(session) -> int:
    """Seed columns for HIS (MySQL), HR (MySQL), and Financial (PG) tables."""
    HIS_HR_FINANCIAL_COLUMNS = {
        # ── ApolloHIS tables ───────────────────────────────────
        "patients": [
            "patient_id", "mrn", "aadhaar_number", "first_name", "last_name",
            "full_name", "date_of_birth", "gender", "blood_group",
            "phone_primary", "phone_secondary", "email",
            "address_line1", "address_line2", "city", "state", "pin_code", "country",
            "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relation",
            "primary_insurance_id", "registration_date", "registration_facility_id",
            "is_vip", "is_active", "deceased_flag", "deceased_date",
            "created_at", "updated_at",
        ],
        "encounters": [
            "encounter_id", "patient_id", "encounter_type", "facility_id",
            "department_id", "unit_id", "treating_provider_id", "attending_provider_id",
            "admission_date", "discharge_date", "expected_discharge",
            "length_of_stay_days", "primary_dx_code", "primary_dx_desc",
            "secondary_dx_codes", "procedure_codes", "admission_source",
            "discharge_disposition", "bed_number", "room_type", "acuity_level",
            "is_readmission", "btg_access_flag", "status", "created_at", "updated_at",
        ],
        "vital_signs": [
            "vital_id", "encounter_id", "patient_id", "recorded_by",
            "recorded_datetime", "temperature_celsius", "heart_rate_bpm",
            "respiratory_rate", "systolic_bp", "diastolic_bp", "spo2_percent",
            "pain_scale", "weight_kg", "height_cm", "bmi", "gcs_score", "created_at",
        ],
        "lab_results": [
            "result_id", "encounter_id", "patient_id", "ordering_provider_id",
            "test_code", "test_name", "test_category", "specimen_type",
            "collected_datetime", "result_datetime", "result_value", "result_unit",
            "reference_range", "abnormal_flag", "status", "created_at",
        ],
        "prescriptions": [
            "prescription_id", "encounter_id", "patient_id", "prescribing_provider_id",
            "medication_name", "generic_name", "dosage", "route", "frequency",
            "start_date", "end_date", "duration_days", "quantity",
            "refills_remaining", "is_active", "discontinued_reason",
            "pharmacy_status", "created_at",
        ],
        "allergies": [
            "allergy_id", "patient_id", "allergen", "allergy_type", "severity",
            "reaction", "onset_date", "reported_by", "is_active", "created_at",
        ],
        "appointments": [
            "appointment_id", "patient_id", "provider_id", "facility_id",
            "department_id", "appointment_datetime", "duration_minutes",
            "appointment_type", "status", "reason_for_visit", "notes",
            "is_telemedicine", "cancellation_reason", "created_at",
        ],
        "clinical_notes": [
            "note_id", "encounter_id", "patient_id", "author_id", "note_type",
            "note_datetime", "note_text", "is_addendum", "parent_note_id",
            "is_signed", "signed_datetime", "created_at",
        ],
        "departments": [
            "department_id", "department_name", "domain", "facility_id",
            "head_employee_id", "floor_number", "extension", "is_active", "created_at",
        ],
        "facilities": [
            "facility_id", "facility_name", "city", "state", "facility_code",
            "total_beds", "nabh_accredited", "jci_accredited", "established_year",
            "address", "phone", "email", "is_active", "created_at", "updated_at",
        ],
        "staff_schedules": [
            "schedule_id", "employee_id", "facility_id", "unit_id",
            "shift_date", "shift_type", "shift_start", "shift_end",
            "is_on_call", "status", "created_at",
        ],
        "units": [
            "unit_id", "unit_name", "department_id", "facility_id",
            "unit_type", "floor_number", "bed_count", "is_active", "created_at",
        ],

        # ── ApolloHR tables ────────────────────────────────────
        "employees": [
            "employee_id", "first_name", "last_name", "full_name",
            "date_of_birth", "gender", "aadhaar_number", "pan_number",
            "phone", "email", "personal_email", "address", "city", "state", "pin_code",
            "employee_type", "designation", "department_id", "facility_id",
            "reporting_manager_id", "hire_date", "termination_date",
            "employment_status", "is_active", "created_at", "updated_at",
        ],
        "payroll": [
            "payroll_id", "employee_id", "pay_period_start", "pay_period_end",
            "basic_salary", "hra", "da", "special_allowance", "overtime_amount",
            "gross_salary", "pf_deduction", "esi_deduction", "professional_tax",
            "tds", "other_deductions", "net_salary", "bank_account_number",
            "ifsc_code", "payment_date", "payment_status", "created_at",
        ],
        "leave_records": [
            "leave_id", "employee_id", "leave_type", "start_date", "end_date",
            "days_count", "reason", "status", "approved_by", "created_at",
        ],
        "certifications": [
            "certification_id", "employee_id", "certification_name",
            "certification_body", "date_obtained", "expiry_date",
            "is_active", "created_at",
        ],
        "credentials": [
            "credential_id", "employee_id", "credential_type", "credential_number",
            "issuing_authority", "issue_date", "expiry_date", "state_of_issue",
            "verification_status", "created_at",
        ],

        # ── apollo_financial tables ────────────────────────────
        "claims": [
            "claim_id", "encounter_id", "patient_id", "payer_id",
            "insurance_plan_id", "claim_date", "claim_type", "total_amount",
            "approved_amount", "denied_amount", "adjustment_amount",
            "primary_dx_code", "procedure_codes", "claim_status",
            "denial_reason", "submitted_date", "adjudicated_date",
            "payment_date", "created_at",
        ],
        "claim_line_items": [
            "line_item_id", "claim_id", "service_date", "service_code",
            "service_description", "quantity", "unit_charge", "total_charge",
            "approved_amount", "denial_code", "created_at",
        ],
        "insurance_plans": [
            "plan_id", "payer_id", "payer_name", "plan_name", "plan_type",
            "coverage_type", "annual_limit", "room_rent_limit", "copay_percent",
            "network_type", "is_active", "created_at",
        ],
        "patient_billing": [
            "billing_id", "patient_id", "encounter_id", "insurance_plan_id",
            "billing_date", "total_charges", "insurance_covered", "patient_copay",
            "discount_amount", "net_amount", "amount_paid", "balance_due",
            "billing_status", "payment_method", "created_at",
        ],
        "payer_contracts": [
            "contract_id", "payer_id", "payer_name", "contract_start_date",
            "contract_end_date", "discount_percent", "payment_terms_days",
            "auto_approval_limit", "requires_preauth", "contract_type",
            "is_active", "created_at",
        ],
        "payments": [
            "payment_id", "claim_id", "billing_id", "payment_date",
            "payment_amount", "payment_source", "payment_method",
            "reference_number", "utr_number", "payment_status", "created_at",
        ],
    }
    count = 0
    for table_name, columns in HIS_HR_FINANCIAL_COLUMNS.items():
        for col_name in columns:
            count += await _upsert_column(session, table_name, col_name)
    return count


async def _seed_users(session) -> int:
    count = 0
    for oid, profile in USER_PROFILES.items():
        await session.run(
            """
            MERGE (u:User {user_id: $oid})
            SET u.display_name = $name, u.email = $email, u.category = $category
            """,
            oid=oid, name=profile["display_name"],
            email=profile.get("email", ""), category=profile.get("category", ""),
        )
        # HAS_ROLE edges
        for role in profile.get("ad_roles", []):
            await session.run(
                """
                MATCH (u:User {user_id: $oid}), (r:Role {name: $role})
                MERGE (u)-[:HAS_ROLE]->(r)
                """,
                oid=oid, role=role,
            )
        count += 1
    return count


async def _seed_policy_edges(session) -> int:
    count = 0
    for role_name, access in ROLE_TABLE_ACCESS.items():
        # ALLOWS_TABLE
        for table in access.get("allow", []):
            await session.run(
                """
                MATCH (r:Role {name: $role}), (t:Table {name: $table})
                MERGE (r)-[:ALLOWS_TABLE]->(t)
                """,
                role=role_name, table=table,
            )
            count += 1

        # DENIES_TABLE
        for table in access.get("deny", []):
            await session.run(
                """
                MATCH (r:Role {name: $role}), (t:Table {name: $table})
                MERGE (r)-[:DENIES_TABLE]->(t)
                """,
                role=role_name, table=table,
            )
            count += 1

    # DENIES_OP for all roles (except admin/compliance)
    admin_roles = {"HIPAA_PRIVACY_OFFICER", "IT_ADMINISTRATOR", "HR_DIRECTOR"}
    for role_name in ROLE_TABLE_ACCESS:
        if role_name in admin_roles:
            ops_to_deny = ["DELETE", "DROP", "ALTER", "TRUNCATE"]
        else:
            ops_to_deny = DENIED_OPS_FOR_ALL
        for op in ops_to_deny:
            await session.run(
                """
                MATCH (r:Role {name: $role}), (o:Operation {name: $op})
                MERGE (r)-[:DENIES_OP]->(o)
                """,
                role=role_name, op=op,
            )
            count += 1

    # ROW_FILTER edges
    for role_name, filters in ROLE_ROW_FILTERS.items():
        for rf in filters:
            await session.run(
                """
                MATCH (r:Role {name: $role})
                MERGE (rf:RowFilter {table: $table, condition: $condition})
                MERGE (r)-[:ROW_FILTER]->(rf)
                """,
                role=role_name, table=rf["table"], condition=rf["condition"],
            )
            count += 1

    return count


async def _seed_role_column_policies(session) -> int:
    """Create (Role)-[:COLUMN_POLICY {visibility}]->(Column) edges."""
    count = 0
    for role_name, tables in ROLE_COLUMN_POLICIES.items():
        for table_name, columns in tables.items():
            for col_name, visibility in columns.items():
                await session.run(
                    """
                    MATCH (r:Role {name: $role}), (c:Column {name: $col, table: $table})
                    MERGE (r)-[cp:COLUMN_POLICY]->(c)
                    SET cp.visibility = $visibility
                    """,
                    role=role_name, col=col_name, table=table_name,
                    visibility=visibility,
                )
                count += 1
    return count


async def main():
    """Entry point -- reads config from environment."""
    from queryvault.app.config import get_settings
    settings = get_settings()

    # Also try to get the Aiven PG DSN for column discovery
    pg_dsn = os.environ.get("XENSQL_PGVECTOR_DSN", None)

    await seed_all(
        neo4j_uri=settings.neo4j_uri,
        neo4j_user=settings.neo4j_user,
        neo4j_password=settings.neo4j_password,
        neo4j_database=settings.neo4j_database,
        pg_dsn=pg_dsn,
    )


if __name__ == "__main__":
    asyncio.run(main())
