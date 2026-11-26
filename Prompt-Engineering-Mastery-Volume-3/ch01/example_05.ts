// invariantGuard.ts
export interface ToolInvocationProposal {
  toolName: string;
  parameters: Record<string, any>;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  tenantId: string;
}

export interface InvariantRule {
  id: string;
  severity: 'HIGH' | 'CRITICAL';
  evaluator: (proposal: ToolInvocationProposal) => boolean;
  errorMessage: string;
}

export class ConstitutionalGuardEngine {
  private invariants: InvariantRule[] = [];

  constructor() {
    this.registerStandardRules();
  }

  private registerStandardRules() {
    // Invariant 001: Block destructive database mutations
    this.invariants.push({
      id: 'INV_001_NO_PROD_DROP',
      severity: 'CRITICAL',
      evaluator: (p) => {
        if (p.toolName === 'execute_database_command') {
          const sql = String(p.parameters.query || '').toLowerCase();
          const forbiddenKeywords = ['drop table', 'truncate', 'alter table', 'drop database'];
          return !forbiddenKeywords.some((kw) => sql.includes(kw));
        }
        return true;
      },
      errorMessage: 'Constitutional Invariant 001 violated: Destructive DDL commands forbidden.'
    });

    // Invariant 002: Enforce network egress boundaries
    this.invariants.push({
      id: 'INV_002_EGRESS_FILTER',
      severity: 'HIGH',
      evaluator: (p) => {
        if (p.toolName === 'http_request') {
          const url = String(p.parameters.url || '');
          const allowedDomains = ['internal.company.net', 'api.monitoring.cloud', 'metrics.corp.internal'];
          return allowedDomains.some((d) => url.includes(d));
        }
        return true;
      },
      errorMessage: 'Constitutional Invariant 002 violated: Unauthorized external network egress domain.'
    });

    // Invariant 003: Enforce strict multi-tenant parameter matching
    this.invariants.push({
      id: 'INV_003_TENANT_ISOLATION',
      severity: 'CRITICAL',
      evaluator: (p) => {
        if (p.parameters.tenant_id) {
          return p.parameters.tenant_id === p.tenantId;
        }
        return true;
      },
      errorMessage: 'Constitutional Invariant 003 violated: Tenant identifier mismatch in tool arguments.'
    });
  }

  public validateProposal(proposal: ToolInvocationProposal): { allowed: boolean; violation?: string; severity?: string } {
    for (const inv of this.invariants) {
      if (!inv.evaluator(proposal)) {
        return {
          allowed: false,
          violation: `[${inv.id}] ${inv.errorMessage}`,
          severity: inv.severity
        };
      }
    }
    return { allowed: true };
  }
}
