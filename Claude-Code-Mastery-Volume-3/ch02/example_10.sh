perf trace -e syscalls:sys_enter_* -o trace.log -- npm test
   ```
2. **Frequency Analysis**: Parse `trace.log` using an automated analysis script that extracts the unique set of required system calls $\mathcal{U}$.
3. **Safety Intersection**: Compare $\mathcal{U}$ against an enterprise prohibited system call blacklist $\mathcal{B}$ (containing dangerous calls like `reboot`, `kexec_load`, `mount`, `bpf`). If $\mathcal{U} \cap \mathcal{B} \neq \emptyset$, investigate the build toolchain for suspicious behavior.
4. **Policy Compilation**: Compile the clean system call set into an optimized BPF byte code profile injected into the container’s OCI runtime configuration.

---

## 6.3 Enterprise Production Deployment: Kubernetes with Kata Containers and gVisor

In large-scale enterprise environments running Kubernetes, platform teams configure multiple **RuntimeClasses** to match isolation tiers to task risk profiles:
