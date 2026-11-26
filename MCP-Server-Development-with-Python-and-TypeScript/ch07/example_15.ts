interface RateLimitWindow {
  count: number;
  resetTime: number;
}

const rateLimitMap = new Map<string, RateLimitWindow>();

function rateLimitMiddleware(req: express.Request, res: express.Response, next: express.NextFunction) {
  const ip = req.ip || req.socket.remoteAddress || "unknown";
  const now = Date.now();
  const windowMs = 60 * 1000;
  const maxRequests = 60;

  const current = rateLimitMap.get(ip);

  if (!current || now > current.resetTime) {
    rateLimitMap.set(ip, { count: 1, resetTime: now + windowMs });
    return next();
  }

  if (current.count >= maxRequests) {
    return res.status(429).json({
      error: "TooManyRequests",
      message: "Rate limit exceeded. Please wait before issuing additional requests.",
      retryAfterSeconds: Math.ceil((current.resetTime - now) / 1000)
    });
  }

  current.count++;
  next();
}

// Attach middleware to POST messages gateway:
app.post("/messages", rateLimitMiddleware, async (req, res) => {
  // Process message...
});
