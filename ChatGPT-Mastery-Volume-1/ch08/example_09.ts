/**
 * Architectural Drill 7: Multi-Tenant Redis Cache Isolation Guard
 */

import { Request, Response, NextFunction } from "express";
import Redis from "ioredis";

export interface TenantScopedRequest extends Request {
  tenantId?: string;
  scopedCache?: {
    get: (key: string) => Promise<string | null>;
    set: (key: string, value: string, ttlSeconds: number) => Promise<"OK">;
  };
}

export function createTenantIsolationMiddleware(masterRedis: Redis) {
  return (req: TenantScopedRequest, res: Response, next: NextFunction): void => {
    // 1. Extract verified tenant identity from upstream authenticated token
    const tenantId = (req as any).user?.tenant_id;
    if (!tenantId || !/^[a-z0-9\-_]{3,48}$/i.test(tenantId)) {
      res.status(403).json({
        error: "invalid_tenant_boundary",
        message: "Request lacks a valid, verified tenant_id claim."
      });
      return;
    }

    req.tenantId = tenantId;

    // 2. Inject strictly namespaced cache wrapper preventing cross-tenant leakage
    req.scopedCache = {
      get: async (key: string): Promise<string | null> => {
        const isolatedKey = `tenant:${tenantId}:cache:${key}`;
        return masterRedis.get(isolatedKey);
      },
      set: async (key: string, value: string, ttlSeconds: number = 3600): Promise<"OK"> => {
        const isolatedKey = `tenant:${tenantId}:cache:${key}`;
        return masterRedis.set(isolatedKey, value, "EX", ttlSeconds);
      }
    };

    next();
  };
}
