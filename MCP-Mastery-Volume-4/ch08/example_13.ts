export interface SchemaDiff {
  type: "REMOVED_TOOL" | "ADDED_REQUIRED_PROP" | "REMOVED_PROP" | "TYPE_MUTATED";
  path: string;
  description: string;
  isBreaking: boolean;
}

export function detectBreakingSchemaChanges(oldTools: any[], newTools: any[]): SchemaDiff[] {
  const diffs: SchemaDiff[] = [];
  const oldToolMap = new Map(oldTools.map((t) => [t.name, t]));
  const newToolMap = new Map(newTools.map((t) => [t.name, t]));

  // 1. Detect removed tools
  for (const [name, oldT] of oldToolMap.entries()) {
    if (!newToolMap.has(name)) {
      diffs.push({
        type: "REMOVED_TOOL",
        path: name,
        description: `Tool '${name}' was deleted or renamed.`,
        isBreaking: true
      });
    }
  }

  // 2. Detect parameter mutations in existing tools
  for (const [name, newT] of newToolMap.entries()) {
    const oldT = oldToolMap.get(name);
    if (!oldT) continue;

    const oldProps = oldT.inputSchema?.properties || {};
    const newProps = newT.inputSchema?.properties || {};
    const oldRequired = new Set(oldT.inputSchema?.required || []);
    const newRequired = new Set(newT.inputSchema?.required || []);

    // Check for newly added required parameters (Breaking!)
    for (const req of newRequired) {
      if (!oldRequired.has(req)) {
        diffs.push({
          type: "ADDED_REQUIRED_PROP",
          path: `${name}.${req}`,
          description: `Parameter '${req}' was marked as required in updated tool '${name}'.`,
          isBreaking: true
        });
      }
    }

    // Check for mutated parameter types (Breaking!)
    for (const [propName, oldDef] of Object.entries(oldProps)) {
      const newDef: any = newProps[propName];
      if (newDef && oldDef && (oldDef as any).type !== newDef.type) {
        diffs.push({
          type: "TYPE_MUTATED",
          path: `${name}.${propName}`,
          description: `Type of parameter '${propName}' mutated from '${(oldDef as any).type}' to '${newDef.type}'.`,
          isBreaking: true
        });
      }
    }
  }

  return diffs;
}
