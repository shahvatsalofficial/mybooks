/**
 * Production Cloudflare Worker Edge License Gate & Telemetry Relay
 * Stack: TypeScript / Cloudflare Workers / Workers KV / Web Crypto API
 */

export interface Env {
  LICENSES_KV: KVNamespace;
  TELEMETRY_ANALYTICS: AnalyticsEngineDataset;
  GATEWAY_SHARED_SECRET: string;
}

interface ActionPayload {
  license_key?: string;
  user_email?: string;
  operation: string;
  parameters: Record<string, unknown>;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // 1. Health Check Endpoint
    if (url.pathname === "/health" && request.method === "GET") {
      return new Response(JSON.stringify({ status: "HEALTHY", edge_region: request.cf?.colo || "global" }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
    }

    // 2. Action Verification Gateway
    if (url.pathname === "/api/v1/edge/dispatch" && request.method === "POST") {
      const authHeader = request.headers.get("Authorization");
      if (!authHeader || authHeader !== `Bearer ${env.GATEWAY_SHARED_SECRET}`) {
        return new Response(JSON.stringify({ error: "unauthorized", message: "Invalid edge gateway credentials." }), {
          status: 401,
          headers: { "Content-Type": "application/json" }
        });
      }

      let payload: ActionPayload;
      try {
        payload = await request.json();
      } catch {
        return new Response(JSON.stringify({ error: "bad_request", message: "Malformed JSON payload." }), {
          status: 400,
          headers: { "Content-Type": "application/json" }
        });
      }

      const { license_key, operation, parameters } = payload;

      // 3. Verify License Key in Cloudflare KV
      if (!license_key) {
        return new Response(
          JSON.stringify({
            error: "license_required",
            message: "This premium action requires an active license key.",
            checkout_url: "https://billing.suhana-enterprises.com/checkout"
          }),
          { status: 402, headers: { "Content-Type": "application/json" } }
        );
      }

      const licenseDataRaw = await env.LICENSES_KV.get(`license:${license_key}`);
      if (!licenseDataRaw) {
        return new Response(
          JSON.stringify({ error: "invalid_license", message: "Supplied license key was not found or has expired." }),
          { status: 403, headers: { "Content-Type": "application/json" } }
        );
      }

      const licenseRecord = JSON.parse(licenseDataRaw);
      if (licenseRecord.status !== "ACTIVE" || licenseRecord.quota_remaining <= 0) {
        return new Response(
          JSON.stringify({ error: "quota_exhausted", message: "Your monthly quota has been exhausted. Please upgrade." }),
          { status: 429, headers: { "Content-Type": "application/json" } }
        );
      }

      // 4. Record Edge Telemetry Non-Blocking via ctx.waitUntil
      ctx.waitUntil(
        (async () => {
          // Decrement Quota in KV
          licenseRecord.quota_remaining -= 1;
          await env.LICENSES_KV.put(`license:${license_key}`, JSON.stringify(licenseRecord));

          // Log to Cloudflare Workers Analytics Engine
          env.TELEMETRY_ANALYTICS.writeDataPoint({
            blobs: [operation, license_key, (request.cf?.country as string) || "UNKNOWN"],
            doubles: [1.0],
            indexes: [licenseRecord.email]
          });
        })()
      );

      // 5. Return Successful Authorization to Custom GPT
      return new Response(
        JSON.stringify({
          status: "AUTHORIZED",
          license_owner: licenseRecord.email,
          tier: licenseRecord.plan_tier,
          remaining_quota: licenseRecord.quota_remaining - 1,
          execution_token: crypto.randomUUID()
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    return new Response(JSON.stringify({ error: "not_found" }), { status: 404 });
  }
};
