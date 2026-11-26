const DeployActionSchema = z.object({
  action: z.literal("DEPLOY"),
  imageTag: z.string().describe("The Docker image tag to deploy (e.g., v2.4.1)"),
  canaryPercent: z.number().min(0).max(100).default(10)
});

const RollbackActionSchema = z.object({
  action: z.literal("ROLLBACK"),
  targetSnapshotId: z.string().uuid().describe("The UUID snapshot ID to restore"),
  forceDrainConnections: z.boolean().default(true)
});

export const ClusterManagementSchema = {
  operation: z.discriminatedUnion("action", [DeployActionSchema, RollbackActionSchema])
    .describe("The cluster operation to perform: either DEPLOY or ROLLBACK")
};
