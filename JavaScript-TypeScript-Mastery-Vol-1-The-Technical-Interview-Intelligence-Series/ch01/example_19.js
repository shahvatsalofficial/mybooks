class SandboxedEventRouter {
    constructor() {
        this.eventQueue = [];
        this.frameBudgetMs = 12; // Leave 4ms buffer for rendering out of the 16ms budget
    }

    registerEvent(sourceApp, callback) {
        this.eventQueue.push({ sourceApp, callback });
    }

    dispatchQueueAsync() {
        const processBatch = (deadline) => {
            // Continue processing events as long as there is time remaining in the current frame
            while (this.eventQueue.length > 0 && deadline.timeRemaining() > 0) {
                const event = this.eventQueue.shift();
                try {
                    // Execute the sub-app callback inside a isolated block
                    event.callback();
                } catch (err) {
                    console.error(`Sub-application ${event.sourceApp} crashed:`, err);
                }
            }

            // If there are still events in the queue, schedule the next batch
            if (this.eventQueue.length > 0) {
                requestIdleCallback(processBatch);
            }
        };

        requestIdleCallback(processBatch);
    }
}
