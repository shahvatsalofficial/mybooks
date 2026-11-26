// A conceptual simplification of the Fiber Node structure
class FiberNode {
    constructor(tag, pendingProps, key) {
        this.tag = tag;                 // Type of work (HostComponent, FunctionComponent, etc.)
        this.key = key;                 // Identity key for diffing
        this.type = null;               // The actual function or class reference
        this.stateNode = null;          // Real DOM node or stateful class instance

        // The Reconciler Singly-Linked Tree Pointers
        this.child = null;              // Pointer to direct child
        this.sibling = null;            // Pointer to sibling
        this.return = null;             // Pointer to parent (return stack context)

        // Work state variables
        this.pendingProps = pendingProps; // Incoming props to evaluate
        this.memoizedProps = null;      // Evaluated props from the last cycle
        this.memoizedState = null;      // Linked list of Hooks state entries
        this.updateQueue = null;        // Pending state transformations

        // Asynchronous scheduling priorities
        this.lanes = 0;                 // Bitmask representing update priorities
        this.childLanes = 0;            // Prioritized lanes within downstream children

        // Double-Buffering mirror pointer
        this.alternate = null;          // Link to the inactive counterpart tree
    }
}
