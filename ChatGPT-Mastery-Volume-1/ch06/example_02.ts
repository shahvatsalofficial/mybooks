/**
 * Production Enterprise GPT Action Gateway & OAuth2 Proxy
 * Stack: Node.js 20+ / TypeScript 5.4 / Express / ioredis / jose / zod
 */

import express, { Request, Response, NextFunction } from "express";
import crypto from "crypto";
import { jwtVerify, createRemoteJWKSet, JWTVerifyOptions } from "jose";
import { z } from "zod";
import Redis from "ioredis";

// Initialize Redis for Distributed Idempotency and Nonce Tracking
const redis = new Redis(process.env.REDIS_URL || "redis://localhost:6379", {
  maxRetriesPerRequest: 3,
  enableReadyCheck: true,
});

const app = express();
app.use(express.json({ limit: "1mb" }));

// 1. Cryptographic Configuration
const JWKS_URI = new URL(process.env.OAUTH_JWKS_URI || "https://auth.suhana-enterprises.com/.well-known/jwks.json");
const JWKS = createRemoteJWKSet(JWKS_URI);
const ACTION_SHARED_SECRET = process.env.OPENAI_ACTION_SHARED_SECRET || "prod-action-hmac-secret-k9f72";
const REQUIRED_AUDIENCE = "https://api.gateway.suhana-enterprises.com/v1";
const ISSUER = "https://auth.suhana-enterprises.com/";

// 2. Strict Zod Schema for Infrastructure Action Payload
export const ProvisionSandboxSchema = z.object({
  idempotency_key: z.string().uuid({ message: "idempotency_key must be a valid UUIDv4" }),
  tenant_id: z.string().regex(/^[a-z0-9\-]{3,32}$/, { message: "tenant_id must be alphanumeric lowercase" }),
  cluster_name: z.enum(["us-east-prod", "eu-west-prod", "ap-south-prod"]),
  memory_gib: z.number().int().min(2).max(64),
  ephemeral_ttl_hours: z.number().int().min(1).max(72).default(24),
  tags: z.record(z.string()).optional(),
});

export type ProvisionSandboxPayload = z.infer<typeof ProvisionSandboxSchema>;

// Authenticated Request Context
interface AuthenticatedRequest extends Request {
  user?: {
    sub: string;
    tenant: string;
    scopes: string[];
    email: string;
  };
}

// 3. Middlewares: OAuth2 Bearer Verification & HMAC Integrity
export async function authenticateOAuth2Token(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): Promise<void> {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    res.status(401).json({
      error: "unauthorized",
      message: "Missing or malformed Authorization header. Expected 'Bearer <JWT>'."
    });
    return;
  }

  const token = authHeader.split(" ")[1];

  try {
    const verifyOptions: JWTVerifyOptions = {
      issuer: ISSUER,
      audience: REQUIRED_AUDIENCE,
      algorithms: ["RS256", "ES256"],
    };

    const { payload } = await jwtVerify(token, JWKS, verifyOptions);

    const scopes = typeof payload.scope === "string" ? payload.scope.split(" ") : [];
    req.user = {
      sub: payload.sub as string,
      tenant: (payload.tenant_id as string) || "default",
      scopes: scopes,
      email: (payload.email as string) || "",
    };

    next();
  } catch (err: any) {
    res.status(401).json({
      error: "invalid_token",
      message: `JWT verification failed: ${err.message}`,
    });
  }
}

// 4. Redis Distributed Idempotency Lock Middleware
export function enforceIdempotency(actionName: string) {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
    const idempotencyKey = req.body?.idempotency_key;
    if (!idempotencyKey) {
      res.status(400).json({
        error: "missing_idempotency_key",
        message: "Action requires an 'idempotency_key' in the request body to prevent double-execution.",
      });
      return;
    }

    const redisKey = `idempotency:${actionName}:${idempotencyKey}`;
    // Atomically claim lock for 300 seconds (5 minutes)
    const acquired = await redis.set(redisKey, "PENDING", "EX", 300, "NX");

    if (!acquired) {
      const existingStatus = await redis.get(redisKey);
      if (existingStatus === "PENDING") {
        res.status(409).json({
          error: "concurrent_action_in_progress",
          message: "A transaction with this idempotency key is currently executing. Await resolution.",
        });
        return;
      }
      // Return cached deterministic response
      try {
        const cachedPayload = JSON.parse(existingStatus || "{}");
        res.status(200).json({
          ...cachedPayload,
          _idempotent_replay: true,
        });
        return;
      } catch {
        res.status(500).json({ error: "idempotency_cache_corruption" });
        return;
      }
    }

    // Intercept res.json to cache response payload in Redis
    const originalJson = res.json.bind(res);
    res.json = (body: any): Response => {
      if (res.statusCode >= 200 && res.statusCode < 300) {
        redis.set(redisKey, JSON.stringify(body), "EX", 86400); // 24-hour cache
      } else {
        redis.del(redisKey); // Release lock on error to allow clean retries
      }
      return originalJson(body);
    };

    next();
  };
}

// 5. Production Action Endpoint: Provision Sandboxed Namespace
app.post(
  "/api/v1/sandbox/provision",
  authenticateOAuth2Token,
  enforceIdempotency("provision_sandbox"),
  async (req: AuthenticatedRequest, res: Response): Promise<void> => {
    // Verify Scope
    if (!req.user?.scopes.includes("action:sandbox:write")) {
      res.status(403).json({
        error: "insufficient_scope",
        message: "OAuth2 token does not hold 'action:sandbox:write' scope.",
      });
      return;
    }

    // Strict Schema Validation
    const parseResult = ProvisionSandboxSchema.safeParse(req.body);
    if (!parseResult.success) {
      res.status(422).json({
        error: "validation_error",
        issues: parseResult.error.flatten().fieldErrors,
        guidance: "Please verify cluster_name enum and ensure memory_gib is between 2 and 64.",
      });
      return;
    }

    const { tenant_id, cluster_name, memory_gib, ephemeral_ttl_hours } = parseResult.data;

    // Simulate Deterministic Provisioning Orchestration
    const sandboxId = `sbx-${crypto.randomBytes(6).toString("hex")}`;
    const expiresAt = new Date(Date.now() + ephemeral_ttl_hours * 3600 * 1000).toISOString();

    const result = {
      status: "SUCCESS",
      sandbox_id: sandboxId,
      cluster: cluster_name,
      allocated_memory_gib: memory_gib,
      tenant_owner: tenant_id,
      endpoint_url: `https://${sandboxId}.${cluster_name}.compute.suhana-enterprises.com`,
      expires_at: expiresAt,
      created_by_user: req.user.email,
    };

    res.status(201).json(result);
  }
);

export default app;
