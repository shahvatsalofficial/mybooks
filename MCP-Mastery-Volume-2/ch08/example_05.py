async def event_loop_monitor(max_acceptable_lag_ms: float = 25.0):
      while True:
          expected = asyncio.get_running_loop().time() + 0.010
          await asyncio.sleep(0.010)
          actual = asyncio.get_running_loop().time()
          lag_ms = (actual - expected) * 1000.0
          if lag_ms > max_acceptable_lag_ms:
              logger.warning(f"CRITICAL: Event loop lag spike detected: {lag_ms:.2f}ms!")
  ```
- If the watchdog records lag exceeding 25ms during the k6 benchmark execution, the CI test suite fails automatically, flagging that a tool handler contains blocking code that must be refactored into an asynchronous coroutine or offloaded to `asyncio.to_thread()`.

---

## 8.5 Automated Multi-Runtime CI/CD Matrix & Container Packaging

Continuous Integration and Continuous Deployment (CI/CD) pipelines represent the final operational checkpoint before code merges into production branches or publishes to package registries. Model Context Protocol servers operate in diverse client runtime environments: human developers execute servers locally on macOS Darwin (ARM64) and Windows (Win32), while cloud agent fleets run on Linux (AMD64/ARM64) Kubernetes pods.

A cross-platform CI/CD pipeline must guarantee that paths, subprocess pipes, line-endings (`\r\n` vs `\n`), and binary dependencies function identically across all environments.

<div class="diagram-container">
<!-- Inlined: diag_ch08_cicd_pipeline.svg -->
<img src="../assets/svg/diag_ch08_cicd_pipeline.svg" alt="Production CI/CD Multi-Runtime Matrix & Automated Release" />
</div>

### 8.5.1 Cross-Platform Path & CRLF Pipeline Gotchas

When building multi-platform MCP servers, three common platform-specific bugs frequently escape local testing and break production deployments:
1. **Windows CRLF Framing Corruption**: On Windows systems, writing to standard output via unconfigured print functions automatically translates newline characters `\n` into carriage return linefeeds `\r\n`. MCP clients reading stdio streams expect single `\n` line delimiters. The stray `\r` character corrupts JSON parsers. Server code must explicitly enforce binary stream output or configure `sys.stdout.reconfigure(newline='\n')`.
2. **POSIX Path Assumptions**: Hardcoding forward slashes `/` in resource URIs or local cache directories causes instant failure on Windows when using OS path libraries. Always use Python's `pathlib.Path` or Node's `node:path`.
3. **Subprocess Signal Handling**: Windows does not implement POSIX `SIGTERM` signals. Terminating child MCP processes on Windows requires issuing `CTRL_BREAK_EVENT` or invoking `TerminateProcess`. CI matrices must include Windows runners to validate graceful shutdown handlers.

### 8.5.2 GitHub Actions Enterprise Workflow Pipeline

The following production GitHub Actions workflow configuration enforces strict static analysis, cross-platform matrix testing across Python versions, headless MCP Inspector verification, and automated cryptographic OIDC publishing.
