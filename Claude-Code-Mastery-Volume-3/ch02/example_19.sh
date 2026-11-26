#!/usr/bin/env bash
# ==============================================================================
# Enterprise Cleanroom Supervisor Daemon
# Author: Vatsal Shah, Lead Enterprise AI Architect
# ==============================================================================
set -euo pipefail
IFS=$'\n\t'

# Configuration Defaults
TASK_ID="${1:-task-$(date +%s)}"
REPO_SRC="${2:-/opt/repositories/core-service}"
CLEANROOM_BASE="/var/lib/agent-cleanrooms/${TASK_ID}"
CGROUP_NAME="agent_${TASK_ID}"
MAX_MEM_BYTES=$((2 * 1024 * 1024 * 1024)) # 2GB RAM Cap
MAX_CPU_QUOTA=200000                     # 2 Cores (200ms per 100ms period)

log() {
    echo -e "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] ${*}"
}

cleanup() {
    log "Initiating atomic cleanroom teardown for: ${TASK_ID}"
    
    # Terminate any lingering processes
    if [ -d "/sys/fs/cgroup/${CGROUP_NAME}" ]; then
        log "Purging cgroup: ${CGROUP_NAME}"
        xargs -a "/sys/fs/cgroup/${CGROUP_NAME}/cgroup.procs" kill -9 2>/dev/null || true
        rmdir "/sys/fs/cgroup/${CGROUP_NAME}" 2>/dev/null || true
    fi

    # Unmount OverlayFS layers
    if mountpoint -q "${CLEANROOM_BASE}/merged"; then
        log "Unmounting merged overlayfs layer..."
        umount -l "${CLEANROOM_BASE}/merged" || true
    fi

    if mountpoint -q "${CLEANROOM_BASE}/scratch"; then
        log "Unmounting tmpfs scratch layer..."
        umount -l "${CLEANROOM_BASE}/scratch" || true
    fi

    # Remove temporary host directories
    rm -rf "${CLEANROOM_BASE}"
    log "✅ Cleanroom ${TASK_ID} destroyed. Host state pristine."
}

trap cleanup EXIT INT TERM

log "🚀 Initializing Ephemeral Cleanroom: ${TASK_ID}"
mkdir -p "${CLEANROOM_BASE}/lower"
mkdir -p "${CLEANROOM_BASE}/scratch"
mkdir -p "${CLEANROOM_BASE}/merged"

# Step 1: Bind mount pristine repository as strictly READ-ONLY
mount --bind -o ro "${REPO_SRC}" "${CLEANROOM_BASE}/lower"
mount -o remount,ro,bind "${CLEANROOM_BASE}/lower"

# Step 2: Mount RAM-backed tmpfs for writable upper layer
mount -t tmpfs -o size=2G,noexec,nosuid,nodev tmpfs "${CLEANROOM_BASE}/scratch"
mkdir -p "${CLEANROOM_BASE}/scratch/upper"
mkdir -p "${CLEANROOM_BASE}/scratch/work"

# Step 3: Combine via OverlayFS
mount -t overlay overlay \
    -o lowerdir="${CLEANROOM_BASE}/lower",upperdir="${CLEANROOM_BASE}/scratch/upper",workdir="${CLEANROOM_BASE}/scratch/work" \
    "${CLEANROOM_BASE}/merged"

# Step 4: Configure Linux cgroup v2 resource envelope
if [ -d "/sys/fs/cgroup" ]; then
    mkdir -p "/sys/fs/cgroup/${CGROUP_NAME}"
    echo "${MAX_MEM_BYTES}" > "/sys/fs/cgroup/${CGROUP_NAME}/memory.max"
    echo "${MAX_CPU_QUOTA} 100000" > "/sys/fs/cgroup/${CGROUP_NAME}/cpu.max"
    echo "100" > "/sys/fs/cgroup/${CGROUP_NAME}/pids.max" # Prevent fork bombs
fi

# Step 5: Launch Claude Code inside gVisor runsc sandbox
log "Executing Claude Code in sandboxed container..."
docker run --rm \
    --runtime=runsc \
    --name "cleanroom_${TASK_ID}" \
    --cgroup-parent="${CGROUP_NAME}" \
    --cap-drop=ALL \
    --security-opt=no-new-privileges \
    --volume="${CLEANROOM_BASE}/merged:/workspace:rw" \
    --workdir="/workspace" \
    claude-cleanroom:latest \
    --prompt "Run unit test suite and refactor failing assertions"

log "✅ Execution completed. Inspecting synthesized diff..."
cd "${CLEANROOM_BASE}/merged"
git diff --stat
