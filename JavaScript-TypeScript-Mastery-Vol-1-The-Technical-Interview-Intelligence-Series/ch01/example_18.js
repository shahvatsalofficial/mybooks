class FederatedSandboxRouter {
    constructor() {
        this.eventQueue = [];
    }

    registerEvent(sourceApp, callback) {
        this.eventQueue.push({ sourceApp, callback });
    }

    dispatchQueueSynchronously() {
        // Uncooperative sub-applications can freeze this main-thread loop!
        while (this.eventQueue.length > 0) {
            const event = this.eventQueue.shift();
            event.callback(); 
        }
    }
}
