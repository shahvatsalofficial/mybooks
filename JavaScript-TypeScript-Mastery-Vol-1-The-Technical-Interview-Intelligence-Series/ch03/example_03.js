class HookNode {
    constructor() {
        this.memoizedState = null;      // The actual resolved hook state value (or reference)
        this.baseState = null;          // Baseline state used during priority calculations
        this.baseQueue = null;          // List of pending actions applied before final render
        this.queue = null;              // Updaters queue currently waiting for application
        this.next = null;               // Pointer to the subsequent Hook node in the list
    }
}
