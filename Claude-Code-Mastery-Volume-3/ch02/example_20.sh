#!/usr/bin/env bash
# ==============================================================================
# Pre-Flight Sandbox Security Verification Suite
# Author: Vatsal Shah, Lead Enterprise AI Architect
# ==============================================================================
set -euo pipefail

PASS=0
FAIL=0

assert_probe() {
    local name="$1"
    local status="$2"
    if [ "$status" -eq 0 ]; then
        echo -e "[e[32mPASSe[0m] $name"
        PASS=$((PASS + 1))
    else
        echo -e "[e[31mFAILe[0m] $name"
        FAIL=$((FAIL + 1))
    fi
}

echo "🔒 Starting Pre-Flight Cleanroom Verification..."

# Probe 1: Verify gVisor Sentry Kernel Signature
if grep -qi "gvisor\|sentry" /proc/version 2>/dev/null; then
    assert_probe "gVisor Sentry Active" 0
else
    assert_probe "gVisor Sentry Active (WARNING: Raw host kernel detected!)" 1
fi

# Probe 2: Verify Default-Deny Egress Firewall
if timeout 2 bash -c "</dev/tcp/8.8.8.8/53" 2>/dev/null; then
    assert_probe "Outbound Egress Blocked (CRITICAL: Connection succeeded!)" 1
else
    assert_probe "Outbound Egress Blocked" 0
fi

# Probe 3: Verify Cloud Metadata Isolation (169.254.169.254)
if timeout 2 curl -s -f "http://169.254.169.254/latest/meta-data/" >/dev/null 2>&1; then
    assert_probe "AWS Metadata Shielded (CRITICAL: IMDS accessible!)" 1
else
    assert_probe "AWS Metadata Shielded" 0
fi

# Probe 4: Verify Dropped Linux Capabilities
CAPS=$(grep "CapEff" /proc/self/status | awk '{print $2}')
if [ "$CAPS" = "0000000000000000" ] || [ "$CAPS" = "0000000000000002" ]; then
    assert_probe "Linux Capabilities Stripped" 0
else
    assert_probe "Linux Capabilities Stripped (Effective: $CAPS)" 1
fi

echo "──────────────────────────────────────────────────────────────────────"
echo "VERIFICATION SUMMARY: $PASS PASSED, $FAIL FAILED"
if [ "$FAIL" -gt 0 ]; then
    echo "❌ SECURITY GATE FAILED: Node cordoned. Halting autonomous runner."
    exit 1
fi

echo "✅ ALL SANDBOX GATES PASSED. Node certified for autonomous agent execution."
exit 0
