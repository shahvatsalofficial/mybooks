aws ec2 modify-instance-metadata-options \
     --instance-id i-0123456789abcdef0 \
     --http-endpoint enabled \
     --http-tokens required \
     --http-put-response-hop-limit 1
   ```
   Setting the hop limit to `1` ensures that packets originating from inside a container namespace (which constitutes an additional network hop) are decremented to TTL 0 and dropped by the Linux kernel, preventing containerized agent processes from reaching the metadata IP under all circumstances.
3. **Block `169.254.169.254` via Iptables**: Explicitly inject a firewall rule dropping all packets to link-local addresses from the container network interface.

---

## 9.3 Scenario 3: The Multi-Arch Cross-Compilation Sandbox

**Context**: You are architecting a CI/CD build platform where autonomous Claude Code agents run on x86_64 host hardware but must compile, link, and test software binaries for ARM64 edge IoT devices using QEMU user-mode emulation (`qemu-aarch64-static`).

**The Attack**: An ingested dependency contains an assembly exploit designed to trigger an escape from QEMU user-mode emulation into the host process space.

**Architectural Drill Questions**:
1. What unique security vulnerabilities arise when combining QEMU user-mode emulation with container sandboxing?
2. How does gVisor’s Sentry interact with multi-architecture binaries running under binary translation?
3. Design an isolated build topology ensuring that a QEMU emulator breakout cannot affect the host system.

**Strategic Solution**:
* Run the QEMU emulator inside a gVisor Sentry container. Even if an attacker achieves arbitrary code execution within the QEMU user-mode process, the resulting system calls are intercepted by Sentry, preventing access to the host x86_64 kernel.
* Deploy hardware ARM64 worker nodes (e.g., AWS Graviton) to eliminate binary emulation entirely, ensuring native execution within native ARM64 gVisor sandboxes.

---

## 9.4 Scenario 4: The Hardware Accelerator (GPU) Pass-Through Dilemma

**Context**: Your enterprise software development team is building autonomous agents that train and test local PyTorch models. To achieve acceptable performance, the agent containers require access to on-premise NVIDIA H100 GPUs via the NVIDIA Container Toolkit.

**The Threat**: Passing GPU device nodes (`/dev/nvidia0`, `/dev/nvidiactl`, `/dev/nvidia-uvm`) into a container grants the container process direct access to the proprietary NVIDIA host kernel driver (`nvidia.ko`), introducing a massive non-virtualized C kernel attack surface.

**Architectural Drill Questions**:
1. Why does gVisor historically struggle with raw GPU device pass-through?
2. How does modern gVisor GPU pass-through (`nvproxy`) preserve security boundaries while allowing CUDA execution?
3. What alternative architectural patterns isolate GPU workloads from autonomous shell execution?

**Strategic Solution**:
* **gVisor nvproxy**: Deploy gVisor’s native `nvproxy` subsystem, which intercepts, validates, and filters all ioctl calls between the container CUDA runtime and the host NVIDIA driver, blocking known driver exploit vectors.
* **RPC-Based Decoupled Compute**: Never mount physical GPU devices directly into the autonomous coding agent container. Instead, run the agent in a pure CPU gVisor sandbox. When the agent needs to execute model training or testing, it dispatches an RPC job to a dedicated, isolated GPU worker pool that accepts only validated tensor inputs, never arbitrary shell scripts.

---

## 10.2 The Lead AI Architect’s 10-Point Sandboxing Audit Checklist
- [ ] 1. **Zero Standard Docker**: 100% of autonomous agent executions run under gVisor (`runsc`) or Firecracker micro-VMs.
- [ ] 2. **KVM Acceleration Active**: `runsc` is configured with `--platform=kvm` for native virtualization performance.
- [ ] 3. **Non-Root Enforcement**: All container processes execute as an unprivileged user (`uid=10001`); root execution is strictly forbidden.
- [ ] 4. **Capabilities Dropped**: Containers execute with `--cap-drop=ALL` with zero privilege escalation permitted.
- [ ] 5. **Read-Only Root Filesystem**: Root OS directories are mounted read-only; writes are restricted to ephemeral `tmpfs` scratchpads.
- [ ] 6. **Docker Socket Severed**: `/var/run/docker.sock` is never mounted under any circumstances.
- [ ] 7. **Default-Deny Egress**: Outbound network traffic is dropped by default; access is restricted to an audited domain allowlist via an inspecting proxy.
- [ ] 8. **DNS Protection**: Direct outbound UDP port 53 traffic is blocked; DNS queries route through a filtering DNS resolver.
- [ ] 9. **Cloud Metadata Shielded**: IMDSv2 is enforced with hop-limit 1; packets to `169.254.169.254` are dropped via iptables.
- [ ] 10. **Automated Cleanroom Destruction**: Workspaces utilize Copy-on-Write overlays; containers and temporary disks are destroyed within 100ms of session exit.

---

## 2.4 Inside the Sentry: Deep Dive into User-Space System Call Emulation

To master the security architecture of gVisor, an enterprise architect must understand how Sentry virtualizes the core subsystems of the Linux kernel without running a single line of privileged host C code.

### 1. Memory Management & Address Spaces
In a standard Linux process, memory management calls (`mmap`, `mprotect`, `munmap`, `brk`) manipulate the host kernel’s memory descriptor (`mm_struct`) and hardware page tables. If an attacker discovers a vulnerability in the host memory management subsystem (such as the infamous Dirty COW race condition in copy-on-write page handling), the attacker can overwrite read-only host memory pages.

Inside gVisor, Sentry maintains its own internal virtual address space representation. When an agent process calls `mmap`:
* Sentry validates the memory protection flags (`PROT_READ`, `PROT_WRITE`, `PROT_EXEC`) against internal policy.
* Sentry maps the memory using its own memory allocator implemented in Go.
* Sentry manages virtual page tables independently of the host. The host kernel sees only that the Sentry process allocated standard anonymous memory.
* Even if an attacker attempts a Dirty COW-style race condition, the race condition executes against Sentry’s Go memory structures, which do not permit arbitrary kernel memory writes.

### 2. The Virtual Filesystem Abstraction (VFS2)
Filesystem operations are historically the most common source of container breakouts. Vulnerabilities in path traversal resolution (such as `openat2()` resolve-flag bugs) frequently allow container processes to break out of chroot jails.

gVisor deploys **VFS2**, a completely re-architected virtual filesystem implementation written in Go:
* Sentry does not allow the container process to interact with host inode structures or raw block devices.
* Path resolution is handled strictly in user space by Sentry’s deterministic path resolution engine.
* Symbolic links, hard links, and relative path traversals (`../../`) are resolved entirely inside Sentry’s memory. If a symlink points outside the container’s mount namespace, Sentry resolves the target strictly relative to the container root, rendering directory traversal escapes physically impossible.

### 3. Process Tree Virtualization & Thread Group Management
When Claude Code spawns parallel build processes, compiler instances, or subagent workers, it invokes `clone()` and `fork()`. 

In standard containers, every spawned process appears in the host operating system’s global process table (visible via `ps aux` on the host, subject to PID namespace mappings). In gVisor:
* Sentry virtualizes the entire process hierarchy inside user space.
* Sentry assigns virtual PIDs, manages thread groups, coordinates signal delivery (`SIGCHLD`, `SIGKILL`), and handles process exit statuses without creating individual host process descriptors.
* To the host operating system, the entire agent container—regardless of whether it runs 1 or 1,000 sub-processes—appears as a single multi-threaded Go application.

---

## 3.4 Building an eBPF Network Enforcement Daemon in Go

To enforce zero-trust network boundaries at bare-metal speeds, enterprise platform engineers deploy custom **eBPF (Extended Berkeley Packet Filter)** programs that attach directly to the Linux kernel network stack.

### The Architectural Flow
Below is a production-grade eBPF network enforcement controller implemented in Go using the `cilium/ebpf` library:
