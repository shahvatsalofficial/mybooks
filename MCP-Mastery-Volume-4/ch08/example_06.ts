import { API, FileInfo } from "jscodeshift";

export default function transformer(file: FileInfo, api: API) {
  const j = api.jscodeshift;
  const root = j(file.source);

  // 1. Rewrite deprecated import paths
  root
    .find(j.ImportDeclaration, { source: { value: "@modelcontextprotocol/sdk" } })
    .forEach((path) => {
      path.node.source.value = "@modelcontextprotocol/sdk/server/index.js";
    });

  // 2. Identify deprecated server.setRequestHandler patterns
  root
    .find(j.CallExpression, {
      callee: {
        object: { name: "server" },
        property: { name: "setRequestHandler" }
      }
    })
    .forEach((path) => {
      // Ensure async handler arrow functions are enforced
      const handlerArg = path.node.arguments[1];
      if (handlerArg && handlerArg.type === "FunctionExpression") {
        handlerArg.async = true;
      }
    });

  return root.toSource();
}
