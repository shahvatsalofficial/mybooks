// High-Precision Architecture: Enforces explicit boundaries and validated literals
const DeploySchema = z.object({
  clusterId: z.enum(["k8s-prod-us-east", "k8s-stage-us-west"]),
  namespace: z.string().regex(/^[a-z0-9-]+$/).max(32),
  replicas: z.number().int().min(1).max(10),
  imageDigest: z.string().regex(/^sha256:[a-f0-9]{64}$/)
});
