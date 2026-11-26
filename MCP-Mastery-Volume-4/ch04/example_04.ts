import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from "@modelcontextprotocol/sdk/types.js";
import * as k8s from "@kubernetes/client-node";

const kc = new k8s.KubeConfig();
kc.loadFromDefault();

const coreApi = kc.makeApiClient(k8s.CoreV1Api);
const appsApi = kc.makeApiClient(k8s.AppsV1Api);

// Allowed Namespaces Whitelist (Blocks kube-system and cert-manager)
const PERMITTED_NAMESPACES = (process.env.K8S_ALLOWED_NAMESPACES || "default,staging,apps").split(",");

function assertNamespacePermitted(ns: string) {
  if (!PERMITTED_NAMESPACES.includes(ns.trim())) {
    throw new Error(`Security Violation: Access to namespace '${ns}' is prohibited by RBAC policy.`);
  }
}

const server = new Server(
  { name: "k8s-operator-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = [
    {
      name: "k8s_get_pods",
      description: "Lists pods in an authorized namespace with phase, restarts, and readiness status.",
      inputSchema: {
        type: "object",
        properties: {
          namespace: { type: "string", description: "Target Kubernetes namespace." }
        },
        required: ["namespace"]
      }
    },
    {
      name: "k8s_diagnose_pod_crashes",
      description: "Correlates pod termination states, container exit codes, and recent cluster events to diagnose CrashLoopBackOff.",
      inputSchema: {
        type: "object",
        properties: {
          namespace: { type: "string", description: "Target namespace." },
          pod_name: { type: "string", description: "Target pod name." }
        },
        required: ["namespace", "pod_name"]
      }
    },
    {
      name: "k8s_rollout_restart_deployment",
      description: "Triggers a zero-downtime rolling restart of a deployment in an authorized namespace.",
      inputSchema: {
        type: "object",
        properties: {
          namespace: { type: "string", description: "Target namespace." },
          deployment_name: { type: "string", description: "Deployment name." }
        },
        required: ["namespace", "deployment_name"]
      }
    }
  ];
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const namespace = String(args?.namespace || "default");
  assertNamespacePermitted(namespace);

  if (name === "k8s_get_pods") {
    try {
      const res = await coreApi.listNamespacedPod({ namespace });
      const pods = res.items.map((p) => {
        const statuses = p.status?.containerStatuses || [];
        const totalRestarts = statuses.reduce((acc, c) => acc + c.restartCount, 0);
        const readyCount = statuses.filter((c) => c.ready).length;

        return {
          name: p.metadata?.name,
          phase: p.status?.phase,
          ready: `${readyCount}/${statuses.length}`,
          restarts: totalRestarts,
          node: p.spec?.nodeName,
          creationTimestamp: p.metadata?.creationTimestamp
        };
      });

      return {
        content: [{ type: "text", text: JSON.stringify(pods, null, 2) }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `K8s List Pods Error: ${err.message}` }] };
    }
  }

  if (name === "k8s_diagnose_pod_crashes") {
    const podName = String(args?.pod_name);
    try {
      const podRes = await coreApi.readNamespacedPod({ name: podName, namespace });
      const pod = podRes;

      // Extract container failure states
      const containerFailures = (pod.status?.containerStatuses || []).map((cs) => ({
        container: cs.name,
        ready: cs.ready,
        restartCount: cs.restartCount,
        lastState: cs.lastState?.terminated ? {
          exitCode: cs.lastState.terminated.exitCode,
          reason: cs.lastState.terminated.reason,
          message: cs.lastState.terminated.message,
          startedAt: cs.lastState.terminated.startedAt,
          finishedAt: cs.lastState.terminated.finishedAt
        } : "None"
      }));

      // Fetch related cluster events
      const eventRes = await coreApi.listNamespacedEvent({
        namespace,
        fieldSelector: `involvedObject.name=${podName}`
      });

      const events = eventRes.items.map((e) => ({
        type: e.type,
        reason: e.reason,
        message: e.message,
        count: e.count,
        lastTimestamp: e.lastTimestamp
      }));

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              pod: podName,
              namespace,
              node: pod.spec?.nodeName,
              containerFailures,
              recentEvents: events
            }, null, 2)
          }
        ]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `K8s Diagnostic Error: ${err.message}` }] };
    }
  }

  if (name === "k8s_rollout_restart_deployment") {
    const deploymentName = String(args?.deployment_name);
    try {
      // Patch pod template annotation to trigger rolling restart
      const patch = {
        spec: {
          template: {
            metadata: {
              annotations: {
                "kubectl.kubernetes.io/restartedAt": new Date().toISOString()
              }
            }
          }
        }
      };

      await appsApi.patchNamespacedDeployment({
        name: deploymentName,
        namespace,
        body: patch
      }, {
        headers: { "Content-Type": "application/strategic-merge-patch+json" }
      });

      return {
        content: [{ type: "text", text: `Successfully triggered rolling restart for deployment '${deploymentName}' in namespace '${namespace}'.` }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `K8s Rollout Restart Error: ${err.message}` }] };
    }
  }

  throw new Error(`Tool ${name} not found`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Kubernetes Operator MCP Server initialized.");
}

main().catch(console.error);
