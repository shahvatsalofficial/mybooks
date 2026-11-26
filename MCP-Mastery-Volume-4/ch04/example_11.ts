function interpretExitCode(code: number): string {
  if (code === 0) return "Success / Clean Exit";
  if (code === 137) return "SIGKILL / OOMKilled: Process terminated due to memory exhaustion or explicit kill.";
  if (code === 143) return "SIGTERM: Process gracefully terminated by Kubernetes pod eviction or scale-down.";
  if (code === 1) return "General Container Error: Uncaught runtime exception or syntax failure.";
  return `Process exited with custom code ${code}.`;
}
