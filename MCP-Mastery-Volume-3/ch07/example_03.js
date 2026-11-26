// sla_tier_router.js — Enterprise SLA Tiering & Weighted Priority Router
const http = require('http');

/**
 * Tenant SLA Configuration Catalog
 */
const TENANT_REGISTRY = {
  'key-gold-fintech-01': { tenant: 'Wealth Management AI', tier: 'GOLD' },
  'key-silver-devops-02': { tenant: 'Developer Platform Team', tier: 'SILVER' },
  'key-bronze-batch-03': { tenant: 'Nightly Analytics Batch', tier: 'BRONZE' }
};

const SLA_TIER_CONFIG = {
  GOLD: {
    weight: 100,
    rateLimitPerSec: 50,
    bucketCapacity: 100,
    maxWaitMs: 2000,
    targetP99Ms: 50
  },
  SILVER: {
    weight: 50,
    rateLimitPerSec: 20,
    bucketCapacity: 40,
    maxWaitMs: 5000,
    targetP99Ms: 200
  },
  BRONZE: {
    weight: 10,
    rateLimitPerSec: 5,
    bucketCapacity: 10,
    maxWaitMs: 10000,
    targetP99Ms: 1000
  }
};

/**
 * In-Memory Token Bucket Rate Limiter per Tenant
 */
class TokenBucket {
  constructor(refillRate, capacity) {
    this.refillRate = refillRate; // tokens per second
    this.capacity = capacity;
    this.tokens = capacity;
    this.lastRefill = Date.now();
  }

  consume() {
    this.refill();
    if (this.tokens >= 1) {
      this.tokens -= 1;
      return true;
    }
    return false;
  }

  refill() {
    const now = Date.now();
    const elapsedSec = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.capacity, this.tokens + elapsedSec * this.refillRate);
    this.lastRefill = now;
  }
}

/**
 * Priority Dispatch Queue with Weighted Fair Scheduling
 */
class PriorityDispatcher {
  constructor(concurrencyLimit = 4) {
    this.concurrencyLimit = concurrencyLimit;
    this.activeWorkers = 0;
    this.queues = {
      GOLD: [],
      SILVER: [],
      BRONZE: []
    };
    this.tokenBuckets = new Map();
  }

  getBucket(apiKey, tier) {
    if (!this.tokenBuckets.has(apiKey)) {
      const cfg = SLA_TIER_CONFIG[tier];
      this.tokenBuckets.set(apiKey, new TokenBucket(cfg.rateLimitPerSec, cfg.bucketCapacity));
    }
    return this.tokenBuckets.get(apiKey);
  }

  enqueue(task) {
    const bucket = this.getBucket(task.apiKey, task.tier);
    if (!bucket.consume()) {
      return task.reject({
        code: 429,
        error: `Rate limit exceeded for tier ${task.tier}. Quota: ${SLA_TIER_CONFIG[task.tier].rateLimitPerSec} req/s`
      });
    }

    this.queues[task.tier].push(task);
    this.schedule();
  }

  schedule() {
    if (this.activeWorkers >= this.concurrencyLimit) return;

    // Weighted Fair Selection: Gold (weight 100), Silver (50), Bronze (10)
    let selectedTier = null;
    const rand = Math.random() * 160;

    if (rand < 100 && this.queues.GOLD.length > 0) {
      selectedTier = 'GOLD';
    } else if (rand < 150 && this.queues.SILVER.length > 0) {
      selectedTier = 'SILVER';
    } else if (this.queues.BRONZE.length > 0) {
      selectedTier = 'BRONZE';
    } else {
      // Fallback to highest non-empty queue
      if (this.queues.GOLD.length > 0) selectedTier = 'GOLD';
      else if (this.queues.SILVER.length > 0) selectedTier = 'SILVER';
      else if (this.queues.BRONZE.length > 0) selectedTier = 'BRONZE';
    }

    if (!selectedTier) return;

    const task = this.queues[selectedTier].shift();
    if (!task) return;

    // Check if task timed out in queue
    const queuedDuration = Date.now() - task.timestamp;
    if (queuedDuration > SLA_TIER_CONFIG[task.tier].maxWaitMs) {
      task.reject({
        code: 504,
        error: `Request timed out in ${task.tier} queue after ${queuedDuration}ms`
      });
      return setImmediate(() => this.schedule());
    }

    this.activeWorkers++;
    const startTime = Date.now();

    task.execute()
      .then(result => {
        const duration = Date.now() - startTime;
        task.resolve({ result, duration, tier: task.tier });
      })
      .catch(err => task.reject({ code: 500, error: err.message }))
      .finally(() => {
        this.activeWorkers--;
        this.schedule();
      });
  }
}

const dispatcher = new PriorityDispatcher(8);

const server = http.createServer((req, res) => {
  if (req.method !== 'POST' || req.url !== '/v1/tools/dispatch') {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ error: 'Endpoint not found' }));
  }

  const apiKey = req.headers['x-api-key'];
  const tenantInfo = TENANT_REGISTRY[apiKey];

  if (!tenantInfo) {
    res.writeHead(401, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ error: 'Unauthorized: Invalid X-API-Key' }));
  }

  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    let payload;
    try {
      payload = JSON.parse(body);
    } catch (err) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ error: 'Invalid JSON payload' }));
    }

    const task = {
      apiKey,
      tier: tenantInfo.tier,
      tenant: tenantInfo.tenant,
      timestamp: Date.now(),
      execute: async () => {
        // Simulate backend tool execution with variable latency
        const execDelay = Math.floor(Math.random() * 30) + 15;
        await new Promise(r => setTimeout(r, execDelay));
        return {
          status: 'completed',
          tool: payload.tool,
          output: `Processed tool execution for ${tenantInfo.tenant}`
        };
      },
      resolve: (data) => {
        res.writeHead(200, {
          'Content-Type': 'application/json',
          'X-SLA-Tier': data.tier,
          'X-Execution-Time-Ms': data.duration.toString()
        });
        res.end(JSON.stringify({ status: 'ok', data: data.result }));
      },
      reject: (err) => {
        res.writeHead(err.code || 500, {
          'Content-Type': 'application/json',
          'X-SLA-Tier': tenantInfo.tier
        });
        res.end(JSON.stringify({ error: err.error }));
      }
    };

    dispatcher.enqueue(task);
  });
});

server.listen(8081, () => {
  console.log('[SLA ROUTER] Priority Gateway active on port 8081');
});
