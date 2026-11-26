export interface ResourceChange {
  address: string;
  type: string;
  actions: string[]; // ["create"], ["delete"], ["update"], etc.
  destroyRisk: "LOW" | "MEDIUM" | "CRITICAL";
}

export function evaluateTerraformPlanRisk(planJson: any): {
  totalChanges: number;
  blastRadiusScore: number;
  criticalDestructions: ResourceChange[];
  approvedForAutoApply: boolean;
} {
  const resourceChanges: any[] = planJson.resource_changes || [];
  let score = 0;
  const criticals: ResourceChange[] = [];

  for (const rc of resourceChanges) {
    const actions = rc.change?.actions || [];
    if (actions.includes("no-op")) continue;

    let actionWeight = 1;
    const isDestroy = actions.includes("delete") || (actions.includes("create") && actions.includes("delete"));
    if (isDestroy) actionWeight = 10;
    else if (actions.includes("create")) actionWeight = 2;

    let tierWeight = 2;
    const type = rc.type || "";
    if (type.includes("database") || type.includes("db_instance") || type.includes("s3_bucket")) {
      tierWeight = 10;
    } else if (type.includes("security_group") || type.includes("route_table") || type.includes("vpc")) {
      tierWeight = 5;
    }

    const itemScore = actionWeight * tierWeight;
    score += itemScore;

    if (isDestroy && tierWeight >= 5) {
      criticals.push({
        address: rc.address,
        type: rc.type,
        actions,
        destroyRisk: "CRITICAL"
      });
    }
  }

  return {
    totalChanges: resourceChanges.length,
    blastRadiusScore: score,
    criticalDestructions: criticals,
    approvedForAutoApply: score < 50 && criticals.length === 0
  };
}
