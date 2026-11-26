export interface DependencyNode {
  id: string;
  index: number;
  lowlink: number;
  onStack: boolean;
  dependencies: string[];
}

export class TarjanCycleDetector {
  private index = 0;
  private stack: DependencyNode[] = [];
  private sccList: string[][] = [];
  private nodes: Map<string, DependencyNode> = new Map();

  public findCycles(graph: Map<string, string[]>): string[][] {
    this.index = 0;
    this.stack = [];
    this.sccList = [];
    this.nodes.clear();

    for (const [id, deps] of graph.entries()) {
      this.nodes.set(id, { id, index: -1, lowlink: -1, onStack: false, dependencies: deps });
    }

    for (const node of this.nodes.values()) {
      if (node.index === -1) {
        this.strongConnect(node);
      }
    }

    // Filter to components containing more than 1 node (true cycles)
    return this.sccList.filter(scc => scc.length > 1);
  }

  private strongConnect(v: DependencyNode): void {
    v.index = this.index;
    v.lowlink = this.index;
    this.index++;
    this.stack.push(v);
    v.onStack = true;

    for (const depId of v.dependencies) {
      const w = this.nodes.get(depId);
      if (!w) continue;

      if (w.index === -1) {
        this.strongConnect(w);
        v.lowlink = Math.min(v.lowlink, w.lowlink);
      } else if (w.onStack) {
        v.lowlink = Math.min(v.lowlink, w.index);
      }
    }

    if (v.lowlink === v.index) {
      const scc: string[] = [];
      let w: DependencyNode;
      do {
        w = this.stack.pop()!;
        w.onStack = false;
        scc.push(w.id);
      } while (w !== v);
      this.sccList.push(scc);
    }
  }
}
