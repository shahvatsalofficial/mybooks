interface OpenAIFunctionTool {
  type: "function";
  function: {
    name: string;
    description?: string;
    strict?: boolean;
    parameters: {
      type: "object";
      properties: Record<string, any>;
      required?: string[];
      additionalProperties?: boolean;
    };
  };
}
