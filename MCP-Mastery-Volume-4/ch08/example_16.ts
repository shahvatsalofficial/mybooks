import Ajv from "ajv";

const ajv = new Ajv();
const schema = {
  type: "object",
  required: ["mcpServers"],
  properties: {
    mcpServers: {
      type: "object",
      additionalProperties: {
        type: "object",
        required: ["command"],
        properties: {
          command: { type: "string" },
          args: { type: "array", items: { type: "string" } },
          env: { type: "object", additionalProperties: { type: "string" } }
        }
      }
    }
  }
};

export function validateClaudeConfig(config: any): boolean {
  const validate = ajv.compile(schema);
  return Boolean(validate(config));
}
