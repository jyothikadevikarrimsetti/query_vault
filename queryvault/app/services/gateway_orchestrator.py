"""QueryVault Gateway Orchestrator -- 5-zone security pipeline wrapping XenSQL.

Security Zones:
  ZONE 1 -- PRE-MODEL:       Identity resolution + prompt injection scan + schema probing check
                              + behavioral fingerprint + threat classification + domain filter
                              + RBAC policy resolution + column scoping
  ZONE 2 -- MODEL BOUNDARY:  Context minimization + XenSQL call (filtered_schema +
                              contextual_rules + question)
  ZONE 3 -- POST-MODEL:      3-gate validation (parallel) + hallucination detection +
                              query rewriting
  ZONE 4 -- EXECUTION:       Circuit breaker check + resource-bounded execution +
                              result sanitization
  ZONE 5 -- CONTINUOUS:      Audit event ingestion + anomaly detection + alert processing

Fail-secure at every zone boundary.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import structlog

from queryvault.app.clients.graph_client import GraphClient
from queryvault.app.clients.xensql_client import XenSQLClient
from queryvault.app.config import Settings
from queryvault.app.models.api import (
    ExecutionResult,
    GatewayQueryRequest,
    GatewayQueryResponse,
    PostModelChecks,
    PreModelChecks,
    SecuritySummary,
)
from queryvault.app.models.enums import ThreatLevel

logger = structlog.get_logger(__name__)


class GatewayOrchestrator:
    """Coordinates the 5-zone security pipeline wrapping XenSQL."""

    # Domain → (engine, database) mapping for multi-database routing
    _DOMAIN_DB_MAP: dict[str, tuple[str, str]] = {
        "HIS": ("mysql", "ApolloHIS"),
        "HR": ("mysql", "ApolloHR"),
        "FINANCIAL": ("postgresql", "apollo_financial"),
        "CLINICAL": ("postgresql", "apollo_analytics"),
        "RESEARCH": ("postgresql", "apollo_analytics"),
        "ADMINISTRATIVE": ("postgresql", "apollo_analytics"),
        "COMPLIANCE": ("postgresql", "apollo_analytics"),
        "IT_OPERATIONS": ("postgresql", "apollo_analytics"),
    }

    def __init__(
        self,
        settings: Settings,
        xensql_client: XenSQLClient,
        graph_client: GraphClient,
        redis: Any = None,
        audit_pool: Any = None,
        target_pg_pool: Any = None,
        target_mysql_pool: Any = None,
        target_pg_pools: dict[str, Any] | None = None,
        target_mysql_pools: dict[str, Any] | None = None,
        circuit_breakers: dict[str, Any] | None = None,
    ) -> None:
        self._settings = settings
        self._xensql = xensql_client
        self._graph = graph_client
        self._redis = redis
        self._audit_pool = audit_pool
        self._target_pg_pool = target_pg_pool
        self._target_mysql_pool = target_mysql_pool
        self._target_pg_pools = target_pg_pools or {}
        self._target_mysql_pools = target_mysql_pools or {}
        self._breakers = circuit_breakers or {}

        # Load attack patterns for injection scanning
        self._attack_patterns = self._load_attack_patterns()

    def _load_attack_patterns(self) -> list[dict]:
        """Load attack patterns from JSON file."""
        patterns_file = self._settings.attack_patterns_file
        if not os.path.isabs(patterns_file):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            patterns_file = os.path.join(base_dir, patterns_file)

        try:
            with open(patterns_file, "r") as f:
                data = json.load(f)
            return [p for p in data.get("patterns", []) if p.get("enabled", True)]
        except Exception as exc:
            logger.warning("attack_patterns_load_failed", error=str(exc))
            return []

    async def process(self, request: GatewayQueryRequest) -> GatewayQueryResponse:
        """Execute the full 5-zone security pipeline."""
        start = time.monotonic()
        request_id = str(uuid.uuid4())
        log = logger.bind(request_id=request_id)
        zones_passed: list[str] = []

        log.info("gateway_started", question_len=len(request.question))

        try:
            return await self._run_zones(request, request_id, log, zones_passed, start)
        except Exception as exc:
            log.error("gateway_error", error=str(exc))
            return GatewayQueryResponse(
                request_id=request_id,
                error="Internal security gateway error",
                security_summary=SecuritySummary(
                    zones_passed=zones_passed,
                    threat_level=ThreatLevel.HIGH,
                ),
            )

    async def _run_zones(
        self,
        request: GatewayQueryRequest,
        request_id: str,
        log: Any,
        zones_passed: list[str],
        start: float,
    ) -> GatewayQueryResponse:

        # ============================================================
        # ZONE 1: PRE-MODEL
        # ============================================================

        # 1a. Identity resolution (JWT validation)
        identity = await self._resolve_identity(request.jwt_token, log)
        if identity is None:
            return GatewayQueryResponse(
                request_id=request_id,
                blocked_reason="Identity verification failed",
                security_summary=SecuritySummary(
                    zones_passed=[],
                    threat_level=ThreatLevel.HIGH,
                ),
            )

        # 1a-ii. Employment status gate (zero-trust: valid token ≠ active employee)
        if isinstance(identity, dict) and identity.get("_blocked"):
            return GatewayQueryResponse(
                request_id=request_id,
                blocked_reason=identity.get("_reason", "Access denied"),
                security_summary=SecuritySummary(
                    zones_passed=[],
                    threat_level=ThreatLevel.HIGH,
                ),
            )

        user_id = identity.get("user_id", "unknown")
        clearance = identity.get("clearance_level", 1)
        domains = identity.get("domains", [])
        roles = identity.get("roles", [])
        log = log.bind(user_id=user_id)

        # 1a-iii. Domain boundary enforcement
        domain_violation = self._check_domain_boundary(request.question, domains)
        if domain_violation:
            log.warning("domain_boundary_blocked", user_domains=domains, violation=domain_violation)
            await self._emit_audit(
                request_id, user_id, "DOMAIN_BLOCKED",
                {"domains": domains, "violation": domain_violation},
            )
            return GatewayQueryResponse(
                request_id=request_id,
                blocked_reason=f"Domain boundary violation: {domain_violation}",
                security_summary=SecuritySummary(
                    zones_passed=[],
                    threat_level=ThreatLevel.MEDIUM,
                ),
            )

        # 1b. Prompt injection scan (200+ patterns)
        injection_result = self._scan_injection(request.question)

        # 1c. Schema probing detection
        probing_result = await self._check_probing(request.question, user_id)

        # 1d. Behavioral fingerprint check
        behavioral_result = await self._check_behavioral(user_id, request.question)

        # 1e. Threat classification (combines all signals)
        threat_level, threat_category, threat_reasons, should_block = self._classify_threat(
            injection_result, probing_result, behavioral_result
        )

        # 1f. Domain filter (from graph)
        allowed_domains = await self._graph.get_user_domains(user_id) if self._graph else domains

        # 1g. RBAC policy resolution (from graph)
        rbac_policy = await self._graph.resolve_rbac_policy(user_id, roles) if self._graph else {}

        # 1h. Column scoping based on clearance + RBAC + per-role overrides
        column_scope = await self._graph.get_column_scope(
            user_id, clearance, allowed_domains, roles=roles
        ) if self._graph else {}

        pre_model = PreModelChecks(
            injection_blocked=injection_result.get("blocked", False),
            injection_risk_score=injection_result.get("risk_score", 0.0),
            injection_flags=injection_result.get("flags", []),
            probing_detected=probing_result.get("is_probing", False),
            probing_score=probing_result.get("score", 0.0),
            behavioral_anomaly_score=behavioral_result.get("anomaly_score", 0.0),
            behavioral_flags=behavioral_result.get("flags", []),
            threat_level=threat_level,
            threat_category=threat_category,
        )

        if should_block:
            log.warning("pre_model_blocked", threat_level=threat_level.value)

            await self._emit_audit(
                request_id, user_id, "THREAT_BLOCKED",
                {"threat_level": threat_level.value, "category": threat_category, "reasons": threat_reasons},
            )

            return GatewayQueryResponse(
                request_id=request_id,
                blocked_reason="; ".join(threat_reasons),
                security_summary=SecuritySummary(
                    pre_model=pre_model,
                    zones_passed=zones_passed,
                    threat_level=threat_level,
                ),
            )

        zones_passed.append("PRE_MODEL")

        # ============================================================
        # ZONE 2: MODEL BOUNDARY -- Call XenSQL
        # ============================================================

        # 2a. Context minimization: build filtered schema + contextual rules
        filtered_schema = await self._minimize_context(rbac_policy, column_scope, allowed_domains)
        contextual_rules = self._build_contextual_rules(rbac_policy, clearance, identity)

        # 2a-bis. Resolve target dialect + database from domains
        resolved_dialect, resolved_database = self._resolve_dialect_and_database(allowed_domains)

        # 2b. XenSQL call
        try:
            pipeline_result = await self._xensql.query(
                question=request.question,
                filtered_schema=filtered_schema,
                contextual_rules=contextual_rules,
                dialect_hint="mixed",
                session_id=request_id,
            )
        except RuntimeError as exc:
            log.error("xensql_failed", error=str(exc))
            return GatewayQueryResponse(
                request_id=request_id,
                error="Pipeline engine unavailable",
                security_summary=SecuritySummary(
                    pre_model=pre_model,
                    zones_passed=zones_passed,
                    threat_level=ThreatLevel.NONE,
                ),
            )

        raw_sql = pipeline_result.get("sql")
        # Re-resolve dialect + database from the actual SQL table references
        if raw_sql:
            resolved_dialect, resolved_database = self._resolve_dialect_and_database(
                allowed_domains, sql=raw_sql,
            )
        if not raw_sql:
            zones_passed.append("MODEL_BOUNDARY")
            return GatewayQueryResponse(
                request_id=request_id,
                error=pipeline_result.get("error", "No SQL generated"),
                security_summary=SecuritySummary(
                    pre_model=pre_model,
                    zones_passed=zones_passed,
                ),
            )

        zones_passed.append("MODEL_BOUNDARY")

        # ============================================================
        # ZONE 3: POST-MODEL -- 3-gate validation (parallel)
        # ============================================================

        # Run all three gates in parallel
        gate_syntax, gate_semantic, gate_permission = await asyncio.gather(
            self._gate_syntax_check(raw_sql),
            self._gate_semantic_check(raw_sql, request.question, filtered_schema),
            self._gate_permission_check(raw_sql, rbac_policy, column_scope),
        )

        # Hallucination detection
        hallucination = self._detect_hallucination(raw_sql, filtered_schema)

        # Query rewriting (masking, row filters)
        rewritten_sql, rewrites = self._rewrite_query(raw_sql, column_scope, rbac_policy)

        gate_results = {
            "syntax": gate_syntax.get("result", "PASS"),
            "semantic": gate_semantic.get("result", "PASS"),
            "permission": gate_permission.get("result", "PASS"),
        }

        violations: list[dict] = []
        violations.extend(gate_syntax.get("violations", []))
        violations.extend(gate_semantic.get("violations", []))
        violations.extend(gate_permission.get("violations", []))

        post_model = PostModelChecks(
            validation_decision="BLOCKED" if any(v == "FAIL" for v in gate_results.values()) else "APPROVED",
            hallucination_detected=hallucination.get("detected", False),
            hallucinated_identifiers=hallucination.get("identifiers", []),
            gate_results=gate_results,
            violations=violations,
            rewrites_applied=rewrites,
        )

        if hallucination.get("detected"):
            log.warning("hallucination_detected", identifiers=hallucination["identifiers"])
            await self._emit_audit(
                request_id, user_id, "HALLUCINATION_BLOCKED",
                {"identifiers": hallucination["identifiers"], "sql": raw_sql[:200]},
            )
            return GatewayQueryResponse(
                request_id=request_id,
                sql=raw_sql,
                blocked_reason=f"SQL references unauthorised objects: {', '.join(hallucination['identifiers'])}",
                security_summary=SecuritySummary(
                    pre_model=pre_model,
                    post_model=post_model,
                    zones_passed=zones_passed,
                    threat_level=ThreatLevel.HIGH,
                ),
            )

        if any(v == "FAIL" for v in gate_results.values()):
            await self._emit_audit(
                request_id, user_id, "VALIDATION_BLOCKED",
                {"violations": violations[:5]},
            )
            return GatewayQueryResponse(
                request_id=request_id,
                sql=raw_sql,
                blocked_reason="SQL failed security validation",
                security_summary=SecuritySummary(
                    pre_model=pre_model,
                    post_model=post_model,
                    zones_passed=zones_passed,
                    threat_level=ThreatLevel.MEDIUM,
                ),
            )

        validated_sql = rewritten_sql or raw_sql
        zones_passed.append("POST_MODEL")

        # ============================================================
        # ZONE 4: EXECUTION -- Circuit breaker + resource-bounded exec
        # ============================================================

        execution = None

        # 4a. Circuit breaker check
        breaker = self._breakers.get("xensql", {})
        if breaker.get("state") == "OPEN":
            log.warning("circuit_breaker_open", service="xensql")
            return GatewayQueryResponse(
                request_id=request_id,
                sql=validated_sql,
                error="Execution service circuit breaker is open",
                security_summary=SecuritySummary(
                    pre_model=pre_model,
                    post_model=post_model,
                    zones_passed=zones_passed,
                    threat_level=ThreatLevel.NONE,
                ),
            )

        # 4b. Enforce per-role result_limit on the SQL before execution
        role_limit = (rbac_policy or {}).get("result_limit")
        if role_limit is not None:
            role_limit = int(role_limit)
            sql_upper = validated_sql.upper().strip().rstrip(";")
            limit_match = re.search(r'LIMIT\s+(\d+)', sql_upper)
            if limit_match:
                existing = int(limit_match.group(1))
                if existing > role_limit:
                    start, end = limit_match.span()
                    validated_sql = validated_sql.rstrip(";").rstrip()
                    validated_sql = validated_sql[:start] + f"LIMIT {role_limit}" + validated_sql[end:]
            else:
                validated_sql = validated_sql.rstrip(";").rstrip() + f" LIMIT {role_limit}"

        # 4c. Dialect correction — fix common MySQL↔PostgreSQL syntax mismatches
        validated_sql = self._correct_dialect(validated_sql, resolved_dialect)

        # 4d. Resource-bounded execution against the target database (dialect-routed)
        execution = await self._execute_sql(
            validated_sql, clearance, log,
            rbac_policy=rbac_policy, dialect=resolved_dialect, database=resolved_database,
        )

        zones_passed.append("EXECUTION")

        # ============================================================
        # ZONE 5: CONTINUOUS -- Audit + anomaly detection + alerts
        # ============================================================

        # 5a. Audit event ingestion
        await self._emit_audit(
            request_id, user_id, "QUERY_COMPLETED",
            {
                "question": request.question[:200],
                "sql": validated_sql[:200],
                "threat_level": threat_level.value,
            },
        )

        # 5b. Anomaly detection (update behavioral profile)
        await self._update_behavioral_profile(user_id, request.question, validated_sql)

        # 5c. Alert processing (check if thresholds exceeded)
        await self._process_alerts(user_id, threat_level, request_id)

        zones_passed.append("CONTINUOUS")

        total_ms = (time.monotonic() - start) * 1000
        log.info(
            "gateway_completed",
            status="SUCCESS",
            latency_ms=f"{total_ms:.1f}",
            zones_passed=zones_passed,
        )

        # Extract results data from execution
        results_data = execution.data if execution else {"rows": [], "columns": []}

        return GatewayQueryResponse(
            request_id=request_id,
            sql=validated_sql,
            results=results_data,
            security_summary=SecuritySummary(
                pre_model=pre_model,
                post_model=post_model,
                execution=execution,
                zones_passed=zones_passed,
                threat_level=threat_level,
                validation_result=post_model.validation_decision,
                execution_status="SUCCESS",
                audit_trail_id=request_id,
            ),
            audit_id=request_id,
        )

    # ── ZONE 1 helpers ───────────────────────────────────────

    async def _resolve_identity(self, jwt_token: str, log: Any) -> dict | None:
        """Resolve JWT to identity context.

        Validates RS256 tokens signed by the demo KeyPair and enriches
        with RBAC metadata (clearance, domains) from the role resolver.
        Also checks employment status against the identity store.
        """
        try:
            import jwt as pyjwt
            from queryvault.app.services.identity.token_validator import LocalKeyPair
            from queryvault.app.services.identity.role_resolver import (
                ROLE_CLEARANCE,
                ROLE_DOMAIN,
            )
            from queryvault.app.services.identity.context_builder import (
                USER_DIRECTORY,
            )
            from queryvault.app.models.enums import ClearanceLevel, EmploymentStatus

            public_key = LocalKeyPair.get().public_key
            payload = pyjwt.decode(
                jwt_token,
                public_key,
                algorithms=["RS256"],
                audience="apollo-zt-pipeline",
                issuer="https://login.microsoftonline.com/apollo-tenant/v2.0",
                options={"verify_exp": True},
            )

            user_id = payload.get("oid", payload.get("sub", "unknown"))

            # Employment status check (zero-trust: valid token ≠ active employee)
            hr_record = USER_DIRECTORY.get(user_id)
            if hr_record and hr_record.employment_status != EmploymentStatus.ACTIVE:
                log.warning(
                    "access_denied_employment_status",
                    user_id=user_id,
                    status=hr_record.employment_status.value,
                )
                return {"_blocked": True, "_reason": f"Employment status: {hr_record.employment_status.value}"}

            # Map JWT claims → identity dict expected by downstream zones
            ad_roles = payload.get("roles", [])
            best_clearance = int(ClearanceLevel.PUBLIC)
            for role in ad_roles:
                lvl = ROLE_CLEARANCE.get(role, ClearanceLevel.PUBLIC)
                if int(lvl) > best_clearance:
                    best_clearance = int(lvl)

            domains = []
            for role in ad_roles:
                d = ROLE_DOMAIN.get(role)
                if d is not None and d.value not in domains:
                    domains.append(d.value)
            if not domains:
                domains = ["ADMINISTRATIVE"]

            identity = {
                "user_id": user_id,
                "clearance_level": best_clearance,
                "domains": domains,
                "roles": ad_roles,
                "name": payload.get("name"),
                "email": payload.get("preferred_username"),
                "groups": payload.get("groups", []),
            }
            log.info("identity_resolved", user_id=identity["user_id"],
                     clearance=best_clearance, domains=domains, roles=ad_roles)
            return identity

        except pyjwt.ExpiredSignatureError:
            log.warning("jwt_expired")
            return None
        except pyjwt.InvalidTokenError as exc:
            log.warning("jwt_invalid", error=str(exc))
            return None
        except ImportError:
            log.error("jwt_library_missing")
            return None
        except Exception as exc:
            log.error("identity_resolution_failed", error=str(exc))
            return None

    def _check_domain_boundary(self, question: str, user_domains: list[str]) -> str | None:
        """Check if the question targets a data domain outside the user's allowed domains.

        Returns a violation description string if blocked, None if allowed.
        CLINICAL and COMPLIANCE users can access clinical data.
        FINANCIAL users cannot access clinical data, and vice versa.
        """
        q = question.lower()

        # Keywords that indicate clinical data access
        clinical_keywords = [
            "patient", "vitals", "diagnosis", "medication", "prescription",
            "lab result", "discharge", "admission", "clinical", "medical",
            "treatment", "symptom", "blood pressure", "heart rate",
            "aadhaar", "health record", "ehr", "emr",
        ]
        # Keywords that indicate financial data access
        financial_keywords = [
            "billing", "invoice", "revenue", "payment", "insurance",
            "claim", "reimbursement", "cost", "charge", "financial",
        ]

        question_targets_clinical = any(kw in q for kw in clinical_keywords)
        question_targets_financial = any(kw in q for kw in financial_keywords)

        # Users with CLINICAL, COMPLIANCE, or RESEARCH domains may access clinical data
        clinical_allowed = any(
            d in ("CLINICAL", "COMPLIANCE", "RESEARCH") for d in user_domains
        )
        financial_allowed = any(
            d in ("FINANCIAL", "COMPLIANCE") for d in user_domains
        )

        if question_targets_clinical and not clinical_allowed:
            return f"User domain(s) {user_domains} cannot access clinical data"

        if question_targets_financial and not financial_allowed:
            return f"User domain(s) {user_domains} cannot access financial data"

        return None

    def _scan_injection(self, question: str) -> dict:
        """Scan for prompt injection attacks using loaded attack patterns."""
        flags: list[str] = []
        max_weight = 0.0

        normalized = question.lower().strip()

        for pattern in self._attack_patterns:
            regex = pattern.get("pattern", "")
            try:
                if re.search(regex, normalized, re.IGNORECASE):
                    flags.append(f"{pattern['category']}: {pattern['description']}")
                    max_weight = max(max_weight, pattern.get("severity_weight", 0.5))
            except re.error:
                continue

        blocked = max_weight >= self._settings.injection_threshold
        return {
            "blocked": blocked,
            "risk_score": min(max_weight, 1.0),
            "flags": flags,
            "patterns_matched": len(flags),
        }

    async def _check_probing(self, question: str, user_id: str) -> dict:
        """Detect schema probing behavior via sliding window in Redis."""
        if not self._redis:
            return {"is_probing": False, "score": 0.0}

        probing_keywords = [
            "show tables", "describe", "information_schema", "schema",
            "columns", "table_name", "sys.tables", "pg_catalog",
            "list tables", "what tables", "show me all",
        ]

        is_probing_query = any(kw in question.lower() for kw in probing_keywords)
        if not is_probing_query:
            return {"is_probing": False, "score": 0.0}

        key = f"qv:probing:{user_id}"
        now = time.time()
        window = self._settings.probing_window_seconds

        try:
            pipe = self._redis.pipeline()
            pipe.zadd(key, {str(now): now})
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zcard(key)
            pipe.expire(key, window * 2)
            results = await pipe.execute()
            count = results[2]
        except Exception:
            return {"is_probing": False, "score": 0.0}

        score = min(count / self._settings.probing_threshold, 1.0)
        return {
            "is_probing": count >= self._settings.probing_threshold,
            "score": score,
            "count_in_window": count,
        }

    async def _check_behavioral(self, user_id: str, question: str) -> dict:
        """Check behavioral fingerprint for anomalies."""
        if not self._redis:
            return {"anomaly_score": 0.0, "flags": []}

        key = f"qv:behavioral:{user_id}"
        flags: list[str] = []

        try:
            profile_data = await self._redis.get(key)
            if not profile_data:
                flags.append("first_time_user")
                return {"anomaly_score": 0.3, "flags": flags}

            profile = json.loads(profile_data)

            # Check time-of-day anomaly
            current_hour = datetime.now(UTC).hour
            usual_hours = profile.get("usual_hours", [])
            if usual_hours and current_hour not in usual_hours:
                flags.append("off_hours_access")

            # Check question complexity deviation
            avg_length = profile.get("avg_question_length", 50)
            if len(question) > avg_length * 3:
                flags.append("unusual_complexity")

            # Check query frequency
            last_query_time = profile.get("last_query_time", 0)
            if time.time() - last_query_time < 1.0:
                flags.append("rapid_fire_queries")

            score = min(len(flags) * 0.25, 1.0)
            return {"anomaly_score": score, "flags": flags}

        except Exception:
            return {"anomaly_score": 0.0, "flags": []}

    def _classify_threat(
        self,
        injection: dict,
        probing: dict,
        behavioral: dict,
    ) -> tuple[ThreatLevel, str | None, list[str], bool]:
        """Combine all pre-model signals into a threat classification."""
        reasons: list[str] = []
        max_score = 0.0

        if injection.get("blocked"):
            reasons.append(f"Injection detected (score={injection['risk_score']:.2f})")
            max_score = max(max_score, injection["risk_score"])

        if probing.get("is_probing"):
            reasons.append(f"Schema probing detected (score={probing['score']:.2f})")
            max_score = max(max_score, probing["score"])

        if behavioral.get("anomaly_score", 0) >= self._settings.behavioral_anomaly_threshold:
            reasons.append(f"Behavioral anomaly (score={behavioral['anomaly_score']:.2f})")
            max_score = max(max_score, behavioral["anomaly_score"])

        if max_score >= 0.9:
            level = ThreatLevel.CRITICAL
        elif max_score >= 0.7:
            level = ThreatLevel.HIGH
        elif max_score >= 0.4:
            level = ThreatLevel.MEDIUM
        elif max_score > 0.0:
            level = ThreatLevel.LOW
        else:
            level = ThreatLevel.NONE

        should_block = level in (ThreatLevel.CRITICAL, ThreatLevel.HIGH)

        category = None
        if injection.get("blocked"):
            category = "INJECTION"
        elif probing.get("is_probing"):
            category = "PROBING"
        elif behavioral.get("anomaly_score", 0) >= self._settings.behavioral_anomaly_threshold:
            category = "BEHAVIORAL_ANOMALY"

        return level, category, reasons, should_block

    # ── ZONE 2 helpers ───────────────────────────────────────

    async def _minimize_context(
        self, rbac_policy: dict, column_scope: dict, allowed_domains: list,
    ) -> dict:
        """Build a filtered schema based on RBAC and column scoping.

        Enriches table entries with their column lists *and data types*
        from Neo4j so the LLM receives proper DDL for SQL generation.
        """
        raw_tables = rbac_policy.get("allowed_tables", [])
        table_names = [
            (t.get("name") or t) if isinstance(t, dict) else str(t)
            for t in raw_tables
        ]

        # Fetch column lists with data types from Neo4j
        table_columns: dict[str, list[dict]] = {}
        if self._graph and table_names:
            table_columns = await self._graph.get_table_columns(
                table_names, include_types=True,
            )

        # Build enriched table entries with columns, types, and engine info
        enriched_tables = []
        for t in raw_tables:
            name = (t.get("name") or t) if isinstance(t, dict) else str(t)
            cols = table_columns.get(name, [])
            # Filter columns based on column_scope visibility (exclude HIDDEN)
            if column_scope:
                cols = [
                    c for c in cols
                    if column_scope.get(c["name"], "VISIBLE") != "HIDDEN"
                ]
            # Include engine type so the LLM generates correct SQL dialect
            engine_info = self._TABLE_DB_MAP.get(name.lower())
            engine = engine_info[0] if engine_info else "postgresql"
            enriched_tables.append({
                "name": name,
                "columns": [
                    {"name": c["name"], "data_type": c.get("data_type", "VARCHAR")}
                    for c in cols
                ],
                "engine": engine,
            })

        return {
            "tables": enriched_tables,
            "columns": column_scope,
            "domains": allowed_domains,
            "row_filters": rbac_policy.get("row_filters", []),
        }

    def _build_contextual_rules(self, rbac_policy: dict, clearance: int, identity: dict | None = None) -> list[str]:
        """Build contextual rules for the NL-to-SQL model."""
        rules: list[str] = []

        # Inject user identity so the LLM can resolve "I", "my", "me"
        if identity:
            from queryvault.app.services.identity.context_builder import USER_DIRECTORY
            user_name = identity.get("name", "")
            user_id = identity.get("user_id", "")
            hr_record = USER_DIRECTORY.get(user_id)
            if user_name and hr_record and hr_record.employee_id:
                rules.append(
                    f'The current user is "{user_name}" with employee/provider ID '
                    f'"{hr_record.employee_id}". When the user says "I", "my", or "me", '
                    f"they refer to this person. Use this ID to filter columns like "
                    f"ordering_provider_id, treating_provider_id, attending_provider_id, "
                    f"prescribing_provider_id, recorded_by, etc."
                )

        if clearance < 3:
            rules.append("Do not access patient-identifiable columns (name, DOB, SSN, MRN).")

        if clearance < 5:
            rules.append("Do not access restricted data (psychotherapy notes, substance abuse records).")

        denied_ops = rbac_policy.get("denied_operations", [])
        if "DELETE" in denied_ops:
            rules.append("Do not generate DELETE statements.")
        if "UPDATE" in denied_ops:
            rules.append("Do not generate UPDATE statements.")
        if "DROP" in denied_ops:
            rules.append("Do not generate DROP statements.")

        rules.append("Always use table aliases for clarity.")
        rules.append("Limit result sets to 1000 rows unless explicitly requested otherwise.")

        # Build per-table engine hints so the LLM uses correct SQL dialect
        pg_tables = []
        mysql_tables = []
        for tbl_name, (engine, _db) in self._TABLE_DB_MAP.items():
            allowed = [t.get("name", t) if isinstance(t, dict) else str(t) for t in rbac_policy.get("allowed_tables", [])]
            allowed_lower = {a.lower() for a in allowed}
            if tbl_name in allowed_lower:
                if engine == "postgresql":
                    pg_tables.append(tbl_name)
                else:
                    mysql_tables.append(tbl_name)

        if pg_tables and mysql_tables:
            rules.append(
                f"IMPORTANT: Tables {', '.join(pg_tables)} are in PostgreSQL — use PostgreSQL syntax (e.g. CURRENT_DATE, AGE(), DATE_TRUNC). "
                f"Tables {', '.join(mysql_tables)} are in MySQL — use MySQL syntax (e.g. CURDATE(), TIMESTAMPDIFF, DATE_FORMAT). "
                f"Generate SQL for the correct dialect based on which tables are referenced."
            )
        elif pg_tables:
            rules.append("All tables are in PostgreSQL. Use PostgreSQL syntax only (e.g. CURRENT_DATE, AGE(), DATE_TRUNC, INTERVAL).")
        elif mysql_tables:
            rules.append("All tables are in MySQL. Use MySQL syntax only (e.g. CURDATE(), TIMESTAMPDIFF, DATE_FORMAT).")

        return rules

    # ── ZONE 3 helpers ───────────────────────────────────────

    async def _gate_syntax_check(self, sql: str) -> dict:
        """Gate 1: Syntax validation -- check SQL is well-formed."""
        violations: list[dict] = []

        # Check for dangerous keywords
        dangerous = ["DROP ", "TRUNCATE ", "ALTER ", "CREATE ", "GRANT ", "REVOKE "]
        sql_upper = sql.upper()
        for kw in dangerous:
            if kw in sql_upper:
                violations.append({
                    "gate": "syntax",
                    "rule": "dangerous_keyword",
                    "detail": f"Statement contains {kw.strip()}",
                })

        # Check for multiple statements (semicolon injection)
        stripped = sql.strip().rstrip(";")
        if ";" in stripped:
            violations.append({
                "gate": "syntax",
                "rule": "multi_statement",
                "detail": "Multiple SQL statements detected",
            })

        return {
            "result": "FAIL" if violations else "PASS",
            "violations": violations,
        }

    async def _gate_semantic_check(self, sql: str, question: str, schema: dict) -> dict:
        """Gate 2: Semantic validation -- SQL aligns with the question intent."""
        violations: list[dict] = []

        # Check for UNION-based injections
        if re.search(r"\bUNION\b.*\bSELECT\b", sql, re.IGNORECASE):
            violations.append({
                "gate": "semantic",
                "rule": "union_injection",
                "detail": "UNION SELECT pattern detected",
            })

        # Check for subqueries accessing information_schema
        if re.search(r"information_schema|pg_catalog|sys\.", sql, re.IGNORECASE):
            violations.append({
                "gate": "semantic",
                "rule": "metadata_access",
                "detail": "Query accesses database metadata tables",
            })

        return {
            "result": "FAIL" if violations else "PASS",
            "violations": violations,
        }

    async def _gate_permission_check(self, sql: str, rbac_policy: dict, column_scope: dict) -> dict:
        """Gate 3: Permission validation -- SQL only accesses allowed resources."""
        violations: list[dict] = []

        denied_tables = rbac_policy.get("denied_tables", [])
        for table in denied_tables:
            if re.search(rf"\b{re.escape(table)}\b", sql, re.IGNORECASE):
                violations.append({
                    "gate": "permission",
                    "rule": "denied_table_access",
                    "detail": f"Query accesses denied table: {table}",
                })

        hidden_columns = [
            col for col, vis in column_scope.items() if vis == "HIDDEN"
        ]
        for col in hidden_columns:
            if re.search(rf"\b{re.escape(col)}\b", sql, re.IGNORECASE):
                violations.append({
                    "gate": "permission",
                    "rule": "hidden_column_access",
                    "detail": f"Query accesses hidden column: {col}",
                })

        return {
            "result": "FAIL" if violations else "PASS",
            "violations": violations,
        }

    def _detect_hallucination(self, sql: str, filtered_schema: dict) -> dict:
        """Detect if SQL references tables/columns not in the filtered schema."""
        logger.debug("hallucination_check_start",
                  sql_preview=sql[:100],
                  num_columns=len(filtered_schema.get("columns", {})),
                  num_tables=len(filtered_schema.get("tables", [])))
        allowed_tables: set[str] = set()
        for t in filtered_schema.get("tables", []):
            if isinstance(t, str):
                allowed_tables.add(t.lower())
            elif isinstance(t, dict):
                name = t.get("table_name", t.get("name", "")).lower()
                if name:
                    allowed_tables.add(name)
                tid = t.get("table_id", "").lower()
                if tid:
                    allowed_tables.add(tid)
                    parts = tid.split(".")
                    if parts:
                        allowed_tables.add(parts[-1])

        # If no schema provided, skip hallucination detection
        if not allowed_tables:
            return {"detected": False, "identifiers": []}

        # Build allowed columns set from BOTH the column_scope dict AND
        # the per-table column lists in the enriched schema.  The visibility
        # dict only contains columns with explicit overrides; columns with
        # the default VISIBLE status are only present in the table entries.
        allowed_columns: set[str] = set()
        columns_data = filtered_schema.get("columns", {})
        if isinstance(columns_data, dict):
            for col_name in columns_data:
                allowed_columns.add(col_name.lower())
        for t in filtered_schema.get("tables", []):
            if not isinstance(t, dict):
                continue
            for col in t.get("columns", []):
                col_name = (col.get("name") or col.get("column_name") or "").lower()
                if col_name:
                    allowed_columns.add(col_name)

        # Build set of table aliases and alias→table mapping from FROM/JOIN
        aliases: set[str] = set()
        alias_to_table: dict[str, str] = {}
        for m in re.finditer(
            r"\b(?:FROM|JOIN)\s+(\w+(?:\.\w+)?)\s+(?:AS\s+)?(\w+)\b",
            sql, re.IGNORECASE,
        ):
            table_name = m.group(1).split(".")[-1].lower()
            alias = m.group(2).lower()
            aliases.add(alias)
            alias_to_table[alias] = table_name

        # Build per-table column sets for qualified (alias.column) checks
        table_columns: dict[str, set[str]] = {}
        for t in filtered_schema.get("tables", []):
            if not isinstance(t, dict):
                continue
            tname = (t.get("name") or t.get("table_name") or "").lower()
            if not tname:
                continue
            cols: set[str] = set()
            for col in t.get("columns", []):
                col_name = (col.get("name") or col.get("column_name") or "").lower()
                if col_name:
                    cols.add(col_name)
            table_columns[tname] = cols

        # Strip string literals and EXTRACT(...FROM...) to avoid false positives
        cleaned_sql = re.sub(r"'[^']*'", "''", sql)
        cleaned_sql = re.sub(r"\bEXTRACT\s*\([^)]*\)", "", cleaned_sql, flags=re.IGNORECASE)

        # Extract table references from SQL (FROM and JOIN clauses)
        table_pattern = r"(?:FROM|JOIN)\s+(\w+)"
        found_tables = re.findall(table_pattern, cleaned_sql, re.IGNORECASE)

        # SQL keywords to skip
        _skip = frozenset({
            "select", "where", "and", "or", "on", "as", "inner", "left",
            "right", "outer", "cross", "full", "natural", "lateral",
        })

        hallucinated: list[str] = []

        # Check tables
        for t in found_tables:
            if (t.lower() not in allowed_tables
                    and t.lower() not in _skip
                    and t.lower() not in aliases):
                hallucinated.append(t)

        # Check columns — extract from SELECT, WHERE, ORDER BY, GROUP BY
        if allowed_columns:
            _sql_keywords = frozenset({
                "select", "from", "where", "and", "or", "not", "in", "is",
                "null", "like", "between", "exists", "case", "when", "then",
                "else", "end", "as", "on", "join", "inner", "left", "right",
                "outer", "cross", "full", "natural", "order", "by", "group",
                "having", "limit", "offset", "union", "all", "distinct",
                "asc", "desc", "count", "sum", "avg", "min", "max", "true",
                "false", "cast", "coalesce", "ifnull", "isnull", "nullif",
                "concat", "substring", "trim", "upper", "lower", "length",
                "replace", "round", "floor", "ceil", "abs", "now", "date",
                "year", "month", "day", "hour", "minute", "second",
                "extract", "interval", "current_date", "current_timestamp",
                "curdate", "getdate", "sysdate", "date_trunc", "date_format",
                "date_add", "date_sub", "datediff", "dateadd", "datepart",
                "to_date", "to_char", "to_number", "to_timestamp",
                "over", "partition", "row_number", "rank", "dense_rank",
                "lag", "lead", "first_value", "last_value",
                "string_agg", "array_agg", "json_agg", "jsonb_agg",
                "sha256", "md5", "power", "sqrt", "mod", "sign",
                "position", "charindex", "patindex", "stuff",
                "timestampdiff", "timestampadd", "timediff",
                "ifnull", "nullif", "greatest", "least",
            })

            # Extract column identifiers: alias.column or bare column refs
            # Match alias.column patterns — check column belongs to the aliased table
            alias_col_pattern = r"\b(\w+)\.(\w+)\b" if aliases else None
            col_refs: set[str] = set()

            if alias_col_pattern:
                for m in re.finditer(alias_col_pattern, cleaned_sql, re.IGNORECASE):
                    alias = m.group(1).lower()
                    col = m.group(2).lower()
                    if alias not in aliases:
                        continue
                    col_refs.add(col)
                    # Per-table check: if alias maps to a known table,
                    # verify the column belongs to THAT table
                    mapped_table = alias_to_table.get(alias)
                    if mapped_table and mapped_table in table_columns:
                        if col not in table_columns[mapped_table]:
                            hallucinated.append(f"column:{alias}.{col} ({col} not in {mapped_table})")

            # Also extract columns from SELECT clause (between SELECT and FROM)
            # Use cleaned_sql so string literals are already stripped
            select_m = re.search(r"\bSELECT\b(.*?)\bFROM\b", cleaned_sql, re.IGNORECASE | re.DOTALL)
            if select_m:
                select_body = select_m.group(1)
                # Strip aliases: remove tokens after AS keyword
                select_body = re.sub(r"\bAS\s+\w+\b", "", select_body, flags=re.IGNORECASE)
                for token in re.findall(r"\b(\w+)\b", select_body):
                    tok = token.lower()
                    if (tok not in _sql_keywords
                            and tok not in aliases
                            and tok not in allowed_tables
                            and not tok.isdigit()):
                        col_refs.add(tok)

            # Also extract columns from WHERE clause
            # Use cleaned_sql so string literals are already stripped
            where_m = re.search(r"\bWHERE\b(.*?)(?:\bORDER\b|\bGROUP\b|\bLIMIT\b|\bHAVING\b|$)", cleaned_sql, re.IGNORECASE | re.DOTALL)
            if where_m:
                where_body = where_m.group(1)
                for token in re.findall(r"\b(\w+)\b", where_body):
                    tok = token.lower()
                    if (tok not in _sql_keywords
                            and tok not in aliases
                            and tok not in allowed_tables
                            and not tok.isdigit()):
                        col_refs.add(tok)

            # Check extracted columns against allowed set
            for col in col_refs:
                if col not in allowed_columns and col not in _sql_keywords:
                    hallucinated.append(f"column:{col}")

        return {
            "detected": len(hallucinated) > 0,
            "identifiers": hallucinated,
        }

    def _rewrite_query(
        self, sql: str, column_scope: dict, rbac_policy: dict,
    ) -> tuple[str, list[str]]:
        """Apply query rewrites for masking and row-level filters."""
        rewritten = sql
        rewrites: list[str] = []

        # Apply column masking
        masked_columns = {
            col: vis for col, vis in column_scope.items() if vis == "MASKED"
        }
        for col in masked_columns:
            esc = re.escape(col)
            # Only mask column references in SELECT clause
            select_m = re.search(r"\bSELECT\b(.*?)\bFROM\b", rewritten, re.IGNORECASE | re.DOTALL)
            if select_m and re.search(rf"\b{esc}\b", select_m.group(1), re.IGNORECASE):
                mask_expr = f"'***MASKED***' AS {col}"
                # Replace alias.column or bare column with mask expression
                new_select = re.sub(
                    rf"\b\w+\.{esc}\b", mask_expr, select_m.group(1), count=1, flags=re.IGNORECASE,
                )
                if new_select == select_m.group(1):
                    # No alias prefix found; replace bare column name
                    new_select = re.sub(rf"\b{esc}\b", mask_expr, select_m.group(1), count=1, flags=re.IGNORECASE)
                rewritten = rewritten[:select_m.start(1)] + new_select + rewritten[select_m.end(1):]
                rewrites.append(f"Column '{col}' masked per policy")

        # Apply row-level filters from RBAC
        # Insert before LIMIT/ORDER BY/GROUP BY to avoid syntax errors
        row_filters = rbac_policy.get("row_filters", [])
        for rf_entry in row_filters:
            condition = rf_entry.get("condition", "")
            if not condition:
                continue
            # Skip conditions with unresolved template placeholders
            if "{{" in condition:
                continue
            sql_upper = rewritten.upper()
            has_where = "WHERE" in sql_upper

            # Find insertion point: before LIMIT, ORDER BY, GROUP BY, or end
            insert_before = len(rewritten.rstrip(";").rstrip())
            for clause in [r"\bLIMIT\b", r"\bORDER\s+BY\b", r"\bGROUP\s+BY\b", r"\bHAVING\b"]:
                m = re.search(clause, rewritten, re.IGNORECASE)
                if m and m.start() < insert_before:
                    insert_before = m.start()

            fragment = f" AND {condition} " if has_where else f" WHERE {condition} "
            rewritten = rewritten[:insert_before].rstrip() + fragment + rewritten[insert_before:]
            rewrites.append(f"Row filter applied: {condition}")

        return rewritten, rewrites

    # ── ZONE 4 helpers ───────────────────────────────────────

    def _correct_dialect(self, sql: str, target_dialect: str) -> str:
        """Fix common SQL dialect mismatches before execution.

        Converts MySQL-specific syntax to PostgreSQL and vice versa
        based on the resolved target dialect.
        """
        if target_dialect == "postgresql":
            return self._mysql_to_postgresql(sql)
        elif target_dialect in ("mysql", "mariadb"):
            return self._postgresql_to_mysql(sql)
        return sql

    def _mysql_to_postgresql(self, sql: str) -> str:
        """Convert common MySQL syntax to PostgreSQL equivalents."""
        result = sql

        # CURDATE() → CURRENT_DATE
        result = re.sub(r"\bCURDATE\s*\(\s*\)", "CURRENT_DATE", result, flags=re.IGNORECASE)

        # NOW() → NOW() (same in both, no change needed)

        # YEAR(expr) → EXTRACT(YEAR FROM expr)
        result = re.sub(
            r"\bYEAR\s*\(([^)]+)\)",
            r"EXTRACT(YEAR FROM \1)",
            result, flags=re.IGNORECASE,
        )

        # MONTH(expr) → EXTRACT(MONTH FROM expr)
        result = re.sub(
            r"\bMONTH\s*\(([^)]+)\)",
            r"EXTRACT(MONTH FROM \1)",
            result, flags=re.IGNORECASE,
        )

        # DAY(expr) → EXTRACT(DAY FROM expr)
        result = re.sub(
            r"\bDAY\s*\(([^)]+)\)",
            r"EXTRACT(DAY FROM \1)",
            result, flags=re.IGNORECASE,
        )

        # DATE_FORMAT(expr, '%Y-%m') → TO_CHAR(expr, 'YYYY-MM')
        def _convert_date_format(m: re.Match) -> str:
            expr = m.group(1)
            fmt = m.group(2)
            pg_fmt = (
                fmt.replace("%Y", "YYYY").replace("%m", "MM").replace("%d", "DD")
                .replace("%H", "HH24").replace("%i", "MI").replace("%s", "SS")
            )
            return f"TO_CHAR({expr}, {pg_fmt})"

        result = re.sub(
            r"\bDATE_FORMAT\s*\(([^,]+),\s*('[^']*')\)",
            _convert_date_format, result, flags=re.IGNORECASE,
        )

        # DATE_SUB(expr, INTERVAL n UNIT) → (expr - INTERVAL 'n UNIT')
        result = re.sub(
            r"\bDATE_SUB\s*\(([^,]+),\s*INTERVAL\s+(\d+)\s+(\w+)\)",
            r"(\1 - INTERVAL '\2 \3')",
            result, flags=re.IGNORECASE,
        )

        # DATE_ADD(expr, INTERVAL n UNIT) → (expr + INTERVAL 'n UNIT')
        result = re.sub(
            r"\bDATE_ADD\s*\(([^,]+),\s*INTERVAL\s+(\d+)\s+(\w+)\)",
            r"(\1 + INTERVAL '\2 \3')",
            result, flags=re.IGNORECASE,
        )

        # TIMESTAMPDIFF(UNIT, start, end) → EXTRACT(EPOCH FROM (end - start)) / divisor
        def _convert_timestampdiff(m: re.Match) -> str:
            unit = m.group(1).upper()
            start = m.group(2)
            end = m.group(3)
            divisors = {"SECOND": 1, "MINUTE": 60, "HOUR": 3600, "DAY": 86400}
            divisor = divisors.get(unit, 86400)
            return f"(EXTRACT(EPOCH FROM ({end} - {start})) / {divisor})"

        result = re.sub(
            r"\bTIMESTAMPDIFF\s*\(\s*(\w+)\s*,\s*([^,]+),\s*([^)]+)\)",
            _convert_timestampdiff, result, flags=re.IGNORECASE,
        )

        # IFNULL(a, b) → COALESCE(a, b)
        result = re.sub(r"\bIFNULL\s*\(", "COALESCE(", result, flags=re.IGNORECASE)

        # LIMIT offset, count → LIMIT count OFFSET offset
        def _convert_limit(m: re.Match) -> str:
            offset = m.group(1).strip()
            count = m.group(2).strip()
            return f"LIMIT {count} OFFSET {offset}"

        result = re.sub(
            r"\bLIMIT\s+(\d+)\s*,\s*(\d+)",
            _convert_limit, result, flags=re.IGNORECASE,
        )

        return result

    def _postgresql_to_mysql(self, sql: str) -> str:
        """Convert common PostgreSQL syntax to MySQL equivalents."""
        result = sql

        # CURRENT_DATE → CURDATE()
        result = re.sub(r"\bCURRENT_DATE\b(?!\s*\()", "CURDATE()", result, flags=re.IGNORECASE)

        # EXTRACT(YEAR FROM expr) → YEAR(expr)
        result = re.sub(
            r"\bEXTRACT\s*\(\s*YEAR\s+FROM\s+([^)]+)\)",
            r"YEAR(\1)", result, flags=re.IGNORECASE,
        )

        # EXTRACT(MONTH FROM expr) → MONTH(expr)
        result = re.sub(
            r"\bEXTRACT\s*\(\s*MONTH\s+FROM\s+([^)]+)\)",
            r"MONTH(\1)", result, flags=re.IGNORECASE,
        )

        # TO_CHAR(expr, 'YYYY-MM') → DATE_FORMAT(expr, '%Y-%m')
        def _convert_to_char(m: re.Match) -> str:
            expr = m.group(1)
            fmt = m.group(2)
            mysql_fmt = (
                fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
                .replace("HH24", "%H").replace("MI", "%i").replace("SS", "%s")
            )
            return f"DATE_FORMAT({expr}, {mysql_fmt})"

        result = re.sub(
            r"\bTO_CHAR\s*\(([^,]+),\s*('[^']*')\)",
            _convert_to_char, result, flags=re.IGNORECASE,
        )

        # expr::type → CAST(expr AS type)
        result = re.sub(
            r"\b(\w+)::(\w+)\b",
            r"CAST(\1 AS \2)", result,
        )

        return result

    def _resolve_target_pool(self, dialect: str, database: str = "") -> tuple[Any, str]:
        """Return (pool, engine_name) for the given dialect and database.

        Routing logic:
          1. Try per-database pool (e.g. apollo_financial, ApolloHIS)
          2. Fall back to generic dialect pool
          3. Fall back to audit pool for PostgreSQL
        """
        if dialect in ("mysql", "mariadb"):
            # Try per-database MySQL pool first
            if database and database in self._target_mysql_pools:
                return self._target_mysql_pools[database], "mysql"
            if self._target_mysql_pool:
                return self._target_mysql_pool, "mysql"
            return None, "mysql"

        # PostgreSQL: try per-database pool first
        if database and database in self._target_pg_pools:
            return self._target_pg_pools[database], "postgresql"
        if self._target_pg_pool:
            return self._target_pg_pool, "postgresql"
        if self._audit_pool:
            return self._audit_pool, "postgresql"
        return None, "postgresql"

    # Table name → (engine, database) lookup for precise routing
    _TABLE_DB_MAP: dict[str, tuple[str, str]] = {
        # ApolloHIS (MySQL)
        "patients": ("mysql", "ApolloHIS"),
        "encounters": ("mysql", "ApolloHIS"),
        "vital_signs": ("mysql", "ApolloHIS"),
        "lab_results": ("mysql", "ApolloHIS"),
        "prescriptions": ("mysql", "ApolloHIS"),
        "allergies": ("mysql", "ApolloHIS"),
        "appointments": ("mysql", "ApolloHIS"),
        "clinical_notes": ("mysql", "ApolloHIS"),
        "departments": ("mysql", "ApolloHIS"),
        "facilities": ("mysql", "ApolloHIS"),
        "staff_schedules": ("mysql", "ApolloHIS"),
        "units": ("mysql", "ApolloHIS"),
        # ApolloHR (MySQL)
        "employees": ("mysql", "ApolloHR"),
        "payroll": ("mysql", "ApolloHR"),
        "leave_records": ("mysql", "ApolloHR"),
        "certifications": ("mysql", "ApolloHR"),
        "credentials": ("mysql", "ApolloHR"),
        # apollo_financial (PostgreSQL)
        "claims": ("postgresql", "apollo_financial"),
        "claim_line_items": ("postgresql", "apollo_financial"),
        "insurance_plans": ("postgresql", "apollo_financial"),
        "patient_billing": ("postgresql", "apollo_financial"),
        "payer_contracts": ("postgresql", "apollo_financial"),
        "payments": ("postgresql", "apollo_financial"),
        # apollo_analytics (PostgreSQL)
        "encounter_summaries": ("postgresql", "apollo_analytics"),
        "population_health": ("postgresql", "apollo_analytics"),
        "quality_metrics": ("postgresql", "apollo_analytics"),
        "research_cohorts": ("postgresql", "apollo_analytics"),
    }

    def _resolve_dialect_and_database(self, allowed_domains: list[str], sql: str = "") -> tuple[str, str]:
        """Determine target engine and database from SQL table references.

        First tries to match table names in the SQL against known tables.
        Falls back to domain-based routing.
        Returns (dialect, database_name).
        """
        if sql:
            # Extract table names from FROM/JOIN clauses
            table_refs = re.findall(r"\b(?:FROM|JOIN)\s+(\w+)", sql, re.IGNORECASE)
            for tbl in table_refs:
                mapping = self._TABLE_DB_MAP.get(tbl.lower())
                if mapping:
                    return mapping

        # Fallback: use domain-based routing
        for domain in allowed_domains:
            mapping = self._DOMAIN_DB_MAP.get(domain.upper())
            if mapping:
                return mapping
        return "postgresql", "apollo_analytics"

    async def _execute_sql(
        self, sql: str, clearance: int, log: Any,
        *, rbac_policy: dict | None = None, dialect: str = "postgresql", database: str = "",
    ) -> ExecutionResult:
        """Execute validated SQL against the target database with safety bounds.

        Routes to PostgreSQL or MySQL based on the dialect detected by XenSQL.

        Guards:
          - Read-only transaction / read-only connection
          - Statement timeout (from settings, default 15s)
          - Row limit (per-role result_limit overrides global default of 1000)
          - Result sanitization (truncate large text fields)
        """
        if not self._settings.execution_enabled:
            log.info("execution_skipped", reason="disabled")
            return ExecutionResult(rows_returned=0, data={"columns": [], "rows": []})

        pool, engine = self._resolve_target_pool(dialect, database)
        if not pool:
            log.warning("execution_skipped", reason=f"no_{engine}_pool")
            return ExecutionResult(rows_returned=0, data={"columns": [], "rows": []})

        # Per-role result_limit overrides the global default
        role_limit = (rbac_policy or {}).get("result_limit")
        row_limit = int(role_limit) if role_limit is not None else self._settings.execution_row_limit
        timeout_ms = self._settings.execution_timeout_ms

        # Enforce row limit: inject LIMIT if missing, or cap existing LIMIT
        sql_stripped = sql.rstrip(";").rstrip()
        sql_upper = sql_stripped.upper()
        if "LIMIT" not in sql_upper:
            sql = sql_stripped + f" LIMIT {row_limit}"
        else:
            import re as _re
            m = _re.search(r'LIMIT\s+(\d+)', sql_upper)
            if m:
                existing_limit = int(m.group(1))
                if existing_limit > row_limit:
                    start, end = m.span()
                    sql = sql_stripped[:start] + f"LIMIT {row_limit}" + sql_stripped[end:]

        if engine == "mysql":
            return await self._execute_mysql(sql, pool, row_limit, timeout_ms, log)
        return await self._execute_postgresql(sql, pool, row_limit, timeout_ms, log)

    async def _execute_postgresql(
        self, sql: str, pool: Any, row_limit: int, timeout_ms: int, log: Any,
    ) -> ExecutionResult:
        """Execute read-only SQL against a PostgreSQL pool (asyncpg)."""
        exec_start = time.monotonic()
        try:
            async with pool.acquire() as conn:
                await conn.execute(f"SET statement_timeout = {int(timeout_ms)}")
                async with conn.transaction(readonly=True):
                    rows = await conn.fetch(sql)

            elapsed_ms = (time.monotonic() - exec_start) * 1000

            if rows:
                columns = list(rows[0].keys())
                data_rows = [
                    {col: self._sanitize_value(row[col]) for col in columns}
                    for row in rows[:row_limit]
                ]
            else:
                columns, data_rows = [], []

            resource_hit = len(rows) >= row_limit
            log.info("sql_executed", engine="postgresql", rows=len(data_rows),
                     columns=len(columns), latency_ms=f"{elapsed_ms:.1f}", resource_hit=resource_hit)

            return ExecutionResult(
                rows_returned=len(data_rows),
                execution_latency_ms=round(elapsed_ms, 1),
                sanitization_applied=True,
                resource_limits_hit=resource_hit,
                data={"columns": columns, "rows": data_rows},
            )

        except asyncio.TimeoutError:
            elapsed_ms = (time.monotonic() - exec_start) * 1000
            log.warning("sql_execution_timeout", engine="postgresql", timeout_ms=timeout_ms)
            return ExecutionResult(
                rows_returned=0, execution_latency_ms=round(elapsed_ms, 1),
                resource_limits_hit=True,
                data={"columns": [], "rows": [], "error": "Query execution timed out"},
            )
        except Exception as exc:
            elapsed_ms = (time.monotonic() - exec_start) * 1000
            log.error("sql_execution_failed", engine="postgresql", error=str(exc))
            return ExecutionResult(
                rows_returned=0,
                execution_latency_ms=round(elapsed_ms, 1),
                data={"columns": [], "rows": [], "error": str(exc)},
            )

    async def _execute_mysql(
        self, sql: str, pool: Any, row_limit: int, timeout_ms: int, log: Any,
    ) -> ExecutionResult:
        """Execute read-only SQL against a MySQL pool (aiomysql)."""
        exec_start = time.monotonic()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await asyncio.wait_for(
                        cursor.execute(sql),
                        timeout=timeout_ms / 1000.0,
                    )
                    desc = cursor.description or []
                    columns = [d[0] for d in desc]
                    records = await cursor.fetchmany(row_limit + 1)

                    truncated = len(records) > row_limit
                    if truncated:
                        records = records[:row_limit]

                    data_rows = [
                        {columns[i]: self._sanitize_value(val) for i, val in enumerate(row)}
                        for row in records
                    ]

            elapsed_ms = (time.monotonic() - exec_start) * 1000
            log.info("sql_executed", engine="mysql", rows=len(data_rows),
                     columns=len(columns), latency_ms=f"{elapsed_ms:.1f}", resource_hit=truncated)

            return ExecutionResult(
                rows_returned=len(data_rows),
                execution_latency_ms=round(elapsed_ms, 1),
                sanitization_applied=True,
                resource_limits_hit=truncated,
                data={"columns": columns, "rows": data_rows},
            )

        except asyncio.TimeoutError:
            elapsed_ms = (time.monotonic() - exec_start) * 1000
            log.warning("sql_execution_timeout", engine="mysql", timeout_ms=timeout_ms)
            return ExecutionResult(
                rows_returned=0, execution_latency_ms=round(elapsed_ms, 1),
                resource_limits_hit=True,
                data={"columns": [], "rows": [], "error": "Query execution timed out"},
            )
        except Exception as exc:
            elapsed_ms = (time.monotonic() - exec_start) * 1000
            log.error("sql_execution_failed", engine="mysql", error=str(exc))
            return ExecutionResult(
                rows_returned=0,
                execution_latency_ms=round(elapsed_ms, 1),
                data={"columns": [], "rows": [], "error": str(exc)},
            )

    @staticmethod
    def _sanitize_value(value: Any) -> Any:
        """Sanitize a database value for safe JSON serialization."""
        if value is None:
            return None
        if isinstance(value, (int, float, bool)):
            return value
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, str):
            # Truncate very long strings
            return value[:2000] if len(value) > 2000 else value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, (bytes, bytearray)):
            return "<binary>"
        # Fallback: convert to string
        return str(value)

    # ── ZONE 5 helpers ───────────────────────────────────────

    async def _emit_audit(
        self, request_id: str, user_id: str,
        event_type: str, payload: dict[str, Any],
    ) -> None:
        """Emit an audit event to PostgreSQL audit store (fire-and-forget)."""
        if not self._audit_pool:
            logger.debug("audit_skipped", reason="no_audit_pool")
            return

        event_id = str(uuid.uuid4())
        severity = "WARNING" if "BLOCK" in event_type else "INFO"

        try:
            async with self._audit_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO audit_events "
                    "(event_id, event_type, source, severity, request_id, user_id, payload, created_at) "
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                    event_id, event_type, "QUERYVAULT", severity,
                    request_id, user_id, json.dumps(payload),
                    datetime.now(UTC),
                )
        except Exception as exc:
            logger.warning("audit_emit_failed", error=str(exc))

    async def _update_behavioral_profile(self, user_id: str, question: str, sql: str) -> None:
        """Update the user's behavioral fingerprint in Redis."""
        if not self._redis:
            return

        key = f"qv:behavioral:{user_id}"
        try:
            profile_data = await self._redis.get(key)
            if profile_data:
                profile = json.loads(profile_data)
            else:
                profile = {
                    "query_count": 0,
                    "avg_question_length": 0,
                    "usual_hours": [],
                    "last_query_time": 0,
                }

            profile["query_count"] = profile.get("query_count", 0) + 1
            total = profile["query_count"]
            old_avg = profile.get("avg_question_length", 0)
            profile["avg_question_length"] = ((old_avg * (total - 1)) + len(question)) / total
            profile["last_query_time"] = time.time()

            current_hour = datetime.now(UTC).hour
            hours = set(profile.get("usual_hours", []))
            hours.add(current_hour)
            profile["usual_hours"] = list(hours)[-24:]

            ttl = self._settings.fingerprint_ttl_days * 86400
            await self._redis.set(key, json.dumps(profile), ex=ttl)
        except Exception as exc:
            logger.warning("behavioral_update_failed", error=str(exc))

    async def _process_alerts(self, user_id: str, threat_level: ThreatLevel, request_id: str) -> None:
        """Check if alert thresholds are exceeded and create alerts if needed."""
        if threat_level in (ThreatLevel.CRITICAL, ThreatLevel.HIGH) and self._audit_pool:
            try:
                alert_id = str(uuid.uuid4())
                async with self._audit_pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO alerts "
                        "(alert_id, severity, status, event_type, user_id, title, description, created_at) "
                        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                        alert_id, threat_level.value, "OPEN", "THREAT_DETECTED",
                        user_id,
                        f"Threat detected: {threat_level.value}",
                        f"Request {request_id} triggered a {threat_level.value} threat alert.",
                        datetime.now(UTC),
                    )
            except Exception as exc:
                logger.warning("alert_creation_failed", error=str(exc))
