#!/usr/bin/env bash
# verify_all.sh — one-command reproduction of every paper claim.
# Usage: bash verify_all.sh        (or: ./verify_all.sh)
#
# Requires only Python 3.9 or newer. No installs needed for the four
# verification scripts; pytest is installed automatically into a local
# .venv for the test suites (187 core + 11 exact-skeleton).

set -u

# --- colors (auto-disabled if not a TTY) ----------------------------------
if [ -t 1 ]; then
    GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; YELLOW=$'\033[0;33m'
    BOLD=$'\033[1m';     DIM=$'\033[2m';    RESET=$'\033[0m'
else
    GREEN=""; RED=""; YELLOW=""; BOLD=""; DIM=""; RESET=""
fi

pass()  { echo "${GREEN}✓ PASS${RESET}  $1"; }
fail()  { echo "${RED}✗ FAIL${RESET}  $1"; }
info()  { echo "${BOLD}→${RESET} $1"; }
warn()  { echo "${YELLOW}!${RESET} $1"; }
hr()    { echo "${DIM}$(printf '%.0s─' {1..60})${RESET}"; }

# Move to the directory containing this script (works no matter where
# the user invokes it from).
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

# --- check Python ----------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 not found. Install Python 3.9 or newer and try again."
    exit 1
fi

PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYMAJOR=$(echo "$PYVER" | cut -d. -f1)
PYMINOR=$(echo "$PYVER" | cut -d. -f2)
if [ "$PYMAJOR" -lt 3 ] || { [ "$PYMAJOR" -eq 3 ] && [ "$PYMINOR" -lt 9 ]; }; then
    fail "Python $PYVER is too old. Need Python 3.9 or newer."
    exit 1
fi
info "Python $PYVER detected."

hr
echo "${BOLD}Barker k=6 — full reproduction${RESET}"
echo "${DIM}Headline: minimal k=6 covering set S = {17881, 1801, 14537, 13417, 18121, 18521}${RESET}"
hr

FAILED=0

# --- environment bootstrap --------------------------------------------------
# Must come BEFORE any step that imports NumPy: the provenance gate and the
# exact-skeleton tests both do, so a Python-only checkout would otherwise fail
# a step the driver is supposed to prepare for. Fail closed: a venv or pip
# failure is a FAILED check, never a silent skip.
if python3 -c 'import pytest, numpy' >/dev/null 2>&1; then
    RUN_PY=python3
elif [ -x ".venv/bin/python3" ] && .venv/bin/python3 -c 'import pytest, numpy' >/dev/null 2>&1; then
    RUN_PY=.venv/bin/python3
else
    warn "pytest/numpy not installed. Setting up a local .venv and installing them..."
    python3 -m venv .venv >/dev/null 2>&1
    if [ ! -x ".venv/bin/python3" ]; then
        fail "Could not create virtual environment (.venv/)."
        FAILED=$((FAILED + 1))
        RUN_PY=""
    else
        .venv/bin/python3 -m pip install --quiet --disable-pip-version-check pytest numpy \
            && RUN_PY=.venv/bin/python3 \
            || { fail "pytest/numpy install failed"; FAILED=$((FAILED + 1)); RUN_PY=""; }
    fi
fi
[ -n "$RUN_PY" ] && info "NumPy-capable interpreter: $RUN_PY"
echo

# --- run the five verification scripts --------------------------------------
# First argument is the interpreter: the four §8.3 scripts are pure stdlib and
# run under bare python3; the provenance gate needs NumPy.
run_step () {
    local py=$1; shift
    local name=$1; shift
    local desc=$1; shift
    info "${BOLD}$name${RESET} — $desc"
    if [ -z "$py" ]; then
        fail "$name (no suitable interpreter — environment bootstrap failed)"
        FAILED=$((FAILED + 1))
        echo
        return
    fi
    if "$py" "$@"; then
        pass "$name"
    else
        fail "$name (exit $?)"
        FAILED=$((FAILED + 1))
    fi
    echo
}

run_step python3 "verify_minimal_k6.py"     "headline k=6 verification (~10s)" \
         barker_k6_bundle/verify_minimal_k6.py

run_step python3 "remark_4_5_1_dn_disconnection.py" "D(N)-disconnection check (<1s)" \
         barker_k6_bundle/remark_4_5_1_dn_disconnection.py

run_step python3 "audit_verify.py"          "91-check numerical audit (~10s)" \
         barker_k6_bundle/audit_verify.py

run_step python3 "audit_cleanroom.py"       "50-check independent reimplementation (~3min)" \
         barker_k6_bundle/audit_cleanroom.py

# Provenance gate: fails on any registered research artifact that is missing or
# whose hash no longer matches its manifest, on release-inventory drift, or on
# an environment that cannot support the artifacts.  Stale provenance means the
# claims listed in that manifest are not currently reproducible, which is a
# release blocker even when every numerical check above passes.
run_step "$RUN_PY" "manifest.py verify"     "provenance + release inventory (~20s)" \
         barker_k6_bundle/research/manifest.py verify

# --- test suites ------------------------------------------------------------
hr
CORE_TESTS=187
EXACT_TESTS=11
info "pytest suites: ${CORE_TESTS} core + ${EXACT_TESTS} exact-skeleton (~3min)"

if [ -n "$RUN_PY" ]; then
    # Pin collection separately. A newly added test must update the public
    # count instead of silently passing under a stale label.
    CORE_COLLECT=$($RUN_PY -m pytest tests/ --collect-only -q 2>&1)
    CORE_STATUS=$?
    EXACT_COLLECT=$($RUN_PY -m pytest skeleton_exact/ --collect-only -q 2>&1)
    EXACT_STATUS=$?
    CORE_FOUND=$(echo "$CORE_COLLECT" | awk '/ collected in /{print $1}' | tail -n 1)
    EXACT_FOUND=$(echo "$EXACT_COLLECT" | awk '/ collected in /{print $1}' | tail -n 1)
    if [ $CORE_STATUS -ne 0 ] || [ $EXACT_STATUS -ne 0 ]; then
        fail "pytest collection"
        [ $CORE_STATUS -ne 0 ] && echo "$CORE_COLLECT"
        [ $EXACT_STATUS -ne 0 ] && echo "$EXACT_COLLECT"
        FAILED=$((FAILED + 1))
    elif [ "$CORE_FOUND" != "$CORE_TESTS" ] || [ "$EXACT_FOUND" != "$EXACT_TESTS" ]; then
        fail "pytest count drift (expected ${CORE_TESTS}+${EXACT_TESTS}, collected ${CORE_FOUND:-?}+${EXACT_FOUND:-?})"
        FAILED=$((FAILED + 1))
    else
        pass "pytest collection (${CORE_TESTS} core + ${EXACT_TESTS} exact-skeleton)"
    fi
    info "Running ${CORE_TESTS} core + ${EXACT_TESTS} exact-skeleton tests via $RUN_PY..."
    if $RUN_PY -m pytest tests/ skeleton_exact/ -q; then
        pass "pytest (${CORE_TESTS} core + ${EXACT_TESTS} exact-skeleton)"
    else
        fail "pytest"
        FAILED=$((FAILED + 1))
    fi
else
    fail "pytest — test suites not run (environment bootstrap failed)"
    FAILED=$((FAILED + 1))
fi

# --- final summary ---------------------------------------------------------
hr
if [ $FAILED -eq 0 ]; then
    echo "${GREEN}${BOLD}ALL CHECKS PASSED${RESET}"
    echo "The minimal k=6 result and every numerical claim of the paper are reproduced."
    exit 0
else
    echo "${RED}${BOLD}$FAILED check(s) FAILED${RESET}"
    echo "Scroll up to see which step failed."
    exit 1
fi
