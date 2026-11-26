/**
 * Architectural Drill 6: Automated Post-Deployment Store Health Checker
 */

const axios = require('axios');

const ENDPOINTS_TO_AUDIT = [
    { name: "Checkout API", url: "https://billing.suhana-enterprises.com/health" },
    { name: "Action Dispatcher", url: "https://api.gateway.suhana-enterprises.com/health" },
    { name: "OpenAPI Specification", url: "https://api.gateway.suhana-enterprises.com/openapi.json" }
];

async function runStoreHealthAudit() {
    console.log("🚀 Starting GPT Store Action Infrastructure Audit...");
    let failureCount = 0;

    for (const ep of ENDPOINTS_TO_AUDIT) {
        const start = Date.now();
        try {
            const resp = await axios.get(ep.url, { timeout: 4000 });
            const latency = Date.now() - start;
            
            if (resp.status === 200 && latency < 1000) {
                console.log(`✅ [PASS] ${ep.name} reachable in ${latency}ms`);
            } else {
                console.error(`⚠️ [WARN] ${ep.name} degraded: Status ${resp.status}, Latency ${latency}ms`);
                failureCount++;
            }
        } catch (err) {
            console.error(`❌ [FAIL] ${ep.name} unreachable: ${err.message}`);
            failureCount++;
        }
    }

    if (failureCount > 0) {
        console.error(`🚨 Audit completed with ${failureCount} failures. Alerting on-call.`);
        process.exit(1);
    } else {
        console.log("🎉 All GPT Store infrastructure endpoints operational!");
    }
}

runStoreHealthAudit();
