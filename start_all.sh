#!/bin/bash
# ============================================================
# QueryVault + XenSQL + Dashboard — Local Dev Launcher
# ============================================================
# Starts all services locally using the project .venv
# Usage: ./start_all.sh
# Stop:  ./stop_all.sh  (or Ctrl+C if running in foreground)
# ============================================================

BASE="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$BASE/logs"
mkdir -p "$LOG_DIR"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'

info()  { echo -e "${GREEN}[START]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN ]${NC} $1"; }
fail()  { echo -e "${RED}[ERROR]${NC} $1"; }

PID_FILE="$BASE/.service_pids"
> "$PID_FILE"

port_in_use() { lsof -ti tcp:"$1" > /dev/null 2>&1; }

# ── Resolve Python from .venv ─────────────────────────────────
PYTHON="$BASE/.venv/bin/python"
if [ ! -f "$PYTHON" ]; then
  fail "Virtual environment not found at $BASE/.venv"
  echo "  Create it with: python3 -m venv .venv && .venv/bin/pip install -r queryvault/requirements.txt -r xensql/requirements.txt aiomysql"
  exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║    QueryVault + XenSQL — Local Development Launcher     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo -e "  Python: ${CYAN}$PYTHON${NC}"
echo ""

# ── 1. Infrastructure (Docker) ────────────────────────────────
info "Checking infrastructure containers..."

start_container() {
  local name="$1"; shift
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${name}$"; then
    echo -e "  ${GREEN}✓${NC} $name already running"
  else
    info "Starting $name..."
    docker run -d --name "$name" "$@" > /dev/null 2>&1 || \
    docker start "$name" > /dev/null 2>&1
    echo -e "  ${GREEN}✓${NC} $name started"
  fi
}

start_container "redis" -p 6379:6379 redis:7-alpine
start_container "neo4j" -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5

echo ""

# ── 2. Python Services ────────────────────────────────────────
start_service() {
  local name="$1" module="$2" port="$3"

  if port_in_use "$port"; then
    info "$name already running on port $port — skipping"
    return 0
  fi

  info "Starting $name on port $port..."
  cd "$BASE"
  PYTHONPATH="$BASE" "$PYTHON" -m uvicorn "$module" --host 0.0.0.0 --port "$port" \
    >> "$LOG_DIR/${name}.log" 2>&1 &
  local pid=$!
  echo "$pid $name" >> "$PID_FILE"
  echo "  PID $pid -> $LOG_DIR/${name}.log"
  sleep 0.5
}

start_service "xensql"     "xensql.app.main:app"     8900
start_service "queryvault" "queryvault.app.main:app"  8950

# ── 3. Dashboard (npm) ────────────────────────────────────────
if port_in_use 3000; then
  info "Dashboard already running on port 3000 — skipping"
else
  if [ -d "$BASE/dashboard" ] && [ -f "$BASE/dashboard/package.json" ]; then
    info "Starting Dashboard on port 3000..."
    cd "$BASE/dashboard"
    npm run dev >> "$LOG_DIR/dashboard.log" 2>&1 &
    DASH_PID=$!
    echo "$DASH_PID dashboard" >> "$PID_FILE"
    echo "  PID $DASH_PID -> $LOG_DIR/dashboard.log"
    cd "$BASE"
  else
    warn "Dashboard directory not found — skipping"
  fi
fi

# ── 4. Health Check ───────────────────────────────────────────
echo ""
info "Waiting 5s for services to boot..."
sleep 5

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    Service Status                       ║"
echo "╚══════════════════════════════════════════════════════════╝"

check_health() {
  local name="$1" url="$2"
  if curl -sf --max-time 3 "$url" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} $name  ($url)"
  else
    echo -e "  ${RED}✗${NC} $name  ($url)"
  fi
}

check_health "Redis"      "redis://localhost:6379"
check_health "Neo4j"      "http://localhost:7474"
check_health "XenSQL"     "http://localhost:8900/health"
check_health "QueryVault" "http://localhost:8950/health"
check_health "Dashboard"  "http://localhost:3000"

echo ""
echo -e "${GREEN}URLs:${NC}"
echo "  Dashboard:  http://localhost:3000"
echo "  XenSQL:     http://localhost:8900/docs"
echo "  QueryVault: http://localhost:8950/docs"
echo "  Neo4j:      http://localhost:7474"
echo ""
echo "Logs: $LOG_DIR/"
echo "PIDs: $PID_FILE"
echo ""
echo "To stop: ./stop_all.sh"
