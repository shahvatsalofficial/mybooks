// schema_transpiler.ts — Enterprise AST Schema Transpiler for MCP Tools
export interface McpToolDefinition {
    name: string;
    description: string;
    inputSchema: Record<string, any>;
}

export interface AnthropicTool {
    name: string;
    description: string;
    input_schema: Record<string, any>;
}

export interface OpenAiTool {
    type: 'function';
    function: {
        name: string;
        description: string;
        parameters: Record<string, any>;
        strict: boolean;
    };
}

export interface GeminiFunctionDeclaration {
    name: string;
    description: string;
    parameters: Record<string, any>;
}

export class SchemaTranspiler {
    /**
     * Recursively dereferences $ref pointers within a schema using root $defs
     */
    public static dereferenceSchema(schema: Record<string, any>): Record<string, any> {
        const rootDefs = schema.$defs || schema.definitions || {};
        
        function inlineRef(node: any): any {
            if (node === null || typeof node !== 'object') {
                return node;
            }

            if (Array.isArray(node)) {
                return node.map(inlineRef);
            }

            if (node.$ref && typeof node.$ref === 'string') {
                const refPath = node.$ref.replace(/^#\/(\$defs|definitions)\//, '');
                if (rootDefs[refPath]) {
                    // Inline and continue recursive resolution
                    return inlineRef(JSON.parse(JSON.stringify(rootDefs[refPath])));
                }
            }

            const result: Record<string, any> = {};
            for (const [key, val] of Object.entries(node)) {
                if (key !== '$defs' && key !== 'definitions') {
                    result[key] = inlineRef(val);
                }
            }
            return result;
        }

        return inlineRef(schema);
    }

    /**
     * Transpiles canonical MCP Tool to Anthropic Tool Spec
     */
    public static toAnthropic(tool: McpToolDefinition): AnthropicTool {
        const dereferenced = this.dereferenceSchema(tool.inputSchema);
        delete dereferenced.$schema;
        delete dereferenced.$id;

        return {
            name: tool.name,
            description: tool.description,
            input_schema: dereferenced
        };
    }

    /**
     * Transpiles canonical MCP Tool to OpenAI Strict Function Calling Spec
     */
    public static toOpenAi(tool: McpToolDefinition): OpenAiTool {
        const dereferenced = this.dereferenceSchema(tool.inputSchema);

        function enforceStrictInvariants(node: any): any {
            if (node === null || typeof node !== 'object' || Array.isArray(node)) {
                return node;
            }

            const copy: Record<string, any> = {};
            delete node.$schema;
            delete node.$id;
            delete node.default; // Unsupported in strict mode

            for (const [key, val] of Object.entries(node)) {
                copy[key] = enforceStrictInvariants(val);
            }

            if (copy.type === 'object') {
                copy.additionalProperties = false;
                const propKeys = Object.keys(copy.properties || {});
                
                // In OpenAI strict mode, every property must appear in required
                const currentRequired = new Set(copy.required || []);
                for (const propKey of propKeys) {
                    if (!currentRequired.has(propKey)) {
                        currentRequired.add(propKey);
                        // Make nullable if it was originally optional
                        const propNode = copy.properties[propKey];
                        if (propNode && propNode.type && !Array.isArray(propNode.type)) {
                            propNode.type = [propNode.type, 'null'];
                        }
                    }
                }
                copy.required = Array.from(currentRequired);
            }

            return copy;
        }

        const strictParameters = enforceStrictInvariants(dereferenced);

        return {
            type: 'function',
            function: {
                name: tool.name,
                description: tool.description,
                parameters: strictParameters,
                strict: true
            }
        };
    }

    /**
     * Transpiles canonical MCP Tool to Google Gemini Function Declaration Spec
     */
    public static toGemini(tool: McpToolDefinition): GeminiFunctionDeclaration {
        const dereferenced = this.dereferenceSchema(tool.inputSchema);

        const typeMap: Record<string, string> = {
            string: 'STRING',
            integer: 'INTEGER',
            number: 'NUMBER',
            boolean: 'BOOLEAN',
            array: 'ARRAY',
            object: 'OBJECT'
        };

        function convertToGeminiAst(node: any): any {
            if (node === null || typeof node !== 'object') {
                return node;
            }

            const out: Record<string, any> = {};

            if (node.type) {
                const rawType = Array.isArray(node.type) ? node.type[0] : node.type;
                out.type = typeMap[rawType.toLowerCase()] || 'OBJECT';
                if (Array.isArray(node.type) && node.type.includes('null')) {
                    out.nullable = true;
                }
            } else {
                out.type = 'OBJECT';
            }

            if (node.description) out.description = node.description;
            if (node.enum) out.enum = node.enum;

            if (node.properties) {
                out.properties = {};
                for (const [k, v] of Object.entries(node.properties)) {
                    out.properties[k] = convertToGeminiAst(v);
                }
            }

            if (node.items) {
                out.items = convertToGeminiAst(node.items);
            }

            if (Array.isArray(node.required) && node.required.length > 0) {
                out.required = node.required;
            }

            return out;
        }

        return {
            name: tool.name,
            description: tool.description,
            parameters: convertToGeminiAst(dereferenced)
        };
    }
}
