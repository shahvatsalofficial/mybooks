import * as k8s from "@kubernetes/client-node";

export async function inspectCustomResourceStatus(
  customApi: k8s.CustomObjectsApi,
  group: string,
  version: string,
  namespace: string,
  plural: string,
  name: string
) {
  const res = await customApi.getNamespacedCustomObject({
    group,
    version,
    namespace,
    plural,
    name
  });

  const obj = res as any;
  const conditions = obj.status?.conditions || [];
  
  return {
    group,
    version,
    kind: obj.kind,
    name: obj.metadata?.name,
    generation: obj.metadata?.generation,
    observedGeneration: obj.status?.observedGeneration,
    isSynced: obj.metadata?.generation === obj.status?.observedGeneration,
    conditions: conditions.map((c: any) => ({
      type: c.type,
      status: c.status,
      reason: c.reason,
      message: c.message,
      lastTransitionTime: c.lastTransitionTime
    }))
  };
}
