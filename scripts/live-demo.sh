#!/usr/bin/env bash
# ABOUTME: Scripted live demo for KubeAuto Day stage presentation (slide 8).
# ABOUTME: Runs the single connected pipeline: Backstage → ArgoCD → Kyverno → Grafana (~90s).

set -eo pipefail

# --- Demo display helpers ---
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
DIM='\033[2m'
NC='\033[0m'

# Simulates typing a command, then runs it
run() {
    echo ""
    echo -ne "${CYAN}❯ ${WHITE}"
    # Type out the command character by character
    for (( i=0; i<${#1}; i++ )); do
        echo -n "${1:$i:1}"
        sleep 0.03
    done
    echo -e "${NC}"
    sleep 0.3
    eval "$1"
}

# Display a section header with pause
section() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  $1${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    sleep "$2"
}

# Pause with a visible countdown
pause() {
    local secs=$1
    local msg="${2:-}"
    if [[ -n "$msg" ]]; then
        echo -e "\n${DIM}  ── $msg ──${NC}"
    fi
    for (( i=secs; i>0; i-- )); do
        echo -ne "\r${DIM}  [${i}s]${NC}  "
        sleep 1
    done
    echo -ne "\r        \r"
}

# Wait for keypress (manual advance)
wait_for_key() {
    echo -e "\n${YELLOW}  ▶ Press any key to continue...${NC}"
    read -n 1 -s -r
}

# ─────────────────────────────────────────────────────────────────────
# DEMO START
# ─────────────────────────────────────────────────────────────────────

clear
echo -e "${GREEN}"
echo "  ╔═══════════════════════════════════════════════════════════╗"
echo "  ║         Platform in Action — Live Demo                   ║"
echo "  ║   Backstage → ArgoCD → Kyverno → Grafana                ║"
echo "  ╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
pause 3 "Starting in 3..."

# ─────────────────────────────────────────────────────────────────────
section "1/4  PLATFORM HEALTH — 27 ArgoCD Applications" 1
# ─────────────────────────────────────────────────────────────────────

run "kubectl get applications -n argocd -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status"

pause 5 "Every component deployed from Git. No kubectl apply."

# ─────────────────────────────────────────────────────────────────────
section "2/4  POLICY ENFORCEMENT — Kyverno blocks non-compliant pods" 1
# ─────────────────────────────────────────────────────────────────────

echo -e "${DIM}  Attempting to deploy a non-compliant pod (no resources, no probes, latest tag)...${NC}"
echo ""
run "kubectl run bad-pod --image=nginx:latest -n apps --dry-run=server 2>&1 || true"

pause 5 "6 policies fired. That pod never reaches the cluster."

# ─────────────────────────────────────────────────────────────────────
section "3/4  DRIFT DETECTION — ArgoCD self-heals in <30s" 1
# ─────────────────────────────────────────────────────────────────────

run "kubectl get service sample-app -n apps -o jsonpath='{.spec.ports[0].name}' && echo '  ← current state'"

echo ""
echo -e "${DIM}  Introducing drift — changing port name to 'drifted'...${NC}"
run "kubectl patch service sample-app -n apps --type=json -p '[{\"op\":\"replace\",\"path\":\"/spec/ports/0/name\",\"value\":\"drifted\"}]'"

pause 3
run "kubectl get service sample-app -n apps -o jsonpath='{.spec.ports[0].name}' && echo '  ← already healed'"

pause 5 "ArgoCD detected the drift and reverted it. Annotation-based tracking."

# ─────────────────────────────────────────────────────────────────────
section "4/4  RUNTIME SECURITY — Falco detects sensitive file read via eBPF" 1
# ─────────────────────────────────────────────────────────────────────

POD=$(kubectl get pods -n apps -l app=sample-app -o jsonpath='{.items[0].metadata.name}')
echo -e "${DIM}  Reading process environment from inside a running container...${NC}"
run "kubectl exec -n apps $POD -- sh -c 'cat /proc/1/environ > /dev/null'"

pause 5 "Waiting for Falco to process the syscall..."

run "kubectl logs -n security -l app.kubernetes.io/name=falco -c falco --tail=20 --since=15s 2>/dev/null | grep sample-app | grep -o '\"rule\":\"[^\"]*\"' | head -3"

pause 5 "eBPF-level detection. No agent in the container. No sidecar."

# ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}"
echo "  ╔═══════════════════════════════════════════════════════════╗"
echo "  ║                    Demo Complete                          ║"
echo "  ║                                                           ║"
echo "  ║   27 apps synced · 6 policies enforced · <30s self-heal  ║"
echo "  ║   eBPF runtime detection · Zero kubectl apply             ║"
echo "  ║                                                           ║"
echo "  ║   github.com/peopleforrester/kubeauto-ai-day             ║"
echo "  ╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
