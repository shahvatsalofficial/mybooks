// Anti-Pattern: Monolithic, polymorphic, loosely typed parameter object
interface DeployInput {
  target: string; // Could be IP, hostname, cluster name, or cloud provider!
  options?: any;  // Unconstrained dictionary invites wild hallucinations
  flags?: string[]; // Model might emit shell flags like ["--force", "-rf"]
}
