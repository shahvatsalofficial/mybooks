// quick_pep.js — Standalone MCP Policy Enforcement Point Interceptor
const crypto = require('crypto');

/**
 * Role-Based Access Control (RBAC) Entitlement Catalog
 */
const POLICY_CATALOG = {
    'support_tier1': {
        allowedTools: ['crm:lookup_ticket', 'knowledge:search_docs'],
        parameterConstraints: {
            'crm:lookup_ticket': (args) => {
                if (!args.ticket_id || typeof args.ticket_id !== 'string') return false;
                // Enforce regex: TICKET-XXXXX only
                return /^TICKET-\d{5,8}$/.test(args.ticket_id);
            }
        }
    },
    'financial_auditor': {
        allowedTools: ['db:query_financials', 'knowledge:search_docs'],
        parameterConstraints: {
            'db:query_financials': (args) => {
                if (!args.sql_query || typeof args.sql_query !== 'string') return false;
                const normalized = args.sql_query.toUpperCase();
                // Enforce read-only constraint
                const forbiddenKeywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'EXEC'];
                for (const kw of forbiddenKeywords) {
                    if (new RegExp(`\\b${kw}\\b`).test(normalized)) {
                        return false; // Forbidden write action detected
                    }
                }
                return true;
            }
        }
    }
};

/**
 * Policy Enforcement Interceptor
 */
class PolicyEnforcementPoint {
    static evaluate(callerIdentity, toolName, args) {
        const policy = POLICY_CATALOG[callerIdentity.role];

        // 1. Check if role exists
        if (!policy) {
            return { allowed: false, reason: `Role '${callerIdentity.role}' has zero tool entitlements.` };
        }

        // 2. Check tool namespace whitelist
        if (!policy.allowedTools.includes(toolName)) {
            return {
                allowed: false,
                reason: `Unauthorized: Role '${callerIdentity.role}' is forbidden from invoking '${toolName}'.`
            };
        }

        // 3. Evaluate parameter-level constraints
        const constraintValidator = policy.parameterConstraints[toolName];
        if (constraintValidator) {
            const isValid = constraintValidator(args);
            if (!isValid) {
                return {
                    allowed: false,
                    reason: `Parameter validation violation: arguments failed policy constraints for '${toolName}'.`
                };
            }
        }

        return { allowed: true, reason: 'Authorized by Policy Enforcement Point.' };
    }
}

// ---------------------------------------------------------------------------
// Verification Test Scenarios
// ---------------------------------------------------------------------------
console.log('=== MCP POLICY ENFORCEMENT POINT (PEP) TEST HARNESS ===\n');

// Test Case 1: Legitimate Scoped Invocation
const legitimateCall = {
    caller: { id: 'agent_auditor_01', role: 'financial_auditor', tenant: 'tenant_acme' },
    tool: 'db:query_financials',
    args: { sql_query: 'SELECT invoice_id, amount_usd FROM invoices WHERE fiscal_year = 2026' }
};

const decision1 = PolicyEnforcementPoint.evaluate(legitimateCall.caller, legitimateCall.tool, legitimateCall.args);
console.log('[Test 1] Legitimate Financial Query:');
console.log(`  Decision: ${decision1.allowed ? 'ALLOW (PASS)' : 'DENY'} | ${decision1.reason}`);

// Test Case 2: Role Unauthorized for Dangerous Tool
const unauthorizedCall = {
    caller: { id: 'agent_support_44', role: 'support_tier1', tenant: 'tenant_acme' },
    tool: 'db:query_financials',
    args: { sql_query: 'SELECT * FROM salaries' }
};

const decision2 = PolicyEnforcementPoint.evaluate(unauthorizedCall.caller, unauthorizedCall.tool, unauthorizedCall.args);
console.log('\n[Test 2] Support Agent Invoking Restricted DB Tool:');
console.log(`  Decision: ${decision2.allowed ? 'ALLOW' : 'DENY (PASS)'} | ${decision2.reason}`);

// Test Case 3: Prompt Injection / Privilege Escalation Attempt (SQL Write)
const maliciousInjectionCall = {
    caller: { id: 'agent_auditor_01', role: 'financial_auditor', tenant: 'tenant_acme' },
    tool: 'db:query_financials',
    args: { sql_query: 'SELECT * FROM invoices; DROP TABLE audit_log; --' }
};

const decision3 = PolicyEnforcementPoint.evaluate(maliciousInjectionCall.caller, maliciousInjectionCall.tool, maliciousInjectionCall.args);
console.log('\n[Test 3] Prompt-Injected Destructive SQL Command:');
console.log(`  Decision: ${decision3.allowed ? 'ALLOW' : 'DENY (PASS)'} | ${decision3.reason}`);
