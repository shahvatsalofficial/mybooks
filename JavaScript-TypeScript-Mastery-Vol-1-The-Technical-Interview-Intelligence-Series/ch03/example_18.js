// Background Worker Thread: offloading computational overhead
self.addEventListener('message', (event) => {
    const { type, buffer } = event.data;
    
    if (type === 'PROCESS') {
        const startTime = Date.now();
        console.log("Worker: Initiating computational parsing pass...");
        
        // 1. Decode the ArrayBuffer back to text in the background thread
        const decoder = new TextDecoder();
        const rawString = decoder.decode(new Uint8Array(buffer));
        
        // 2. Parse the JSON payload on the worker thread
        const parsedData = JSON.parse(rawString);
        
        // 3. Execute heavy mathematical analysis
        const metrics = executeHeavyAnalysisBackground(parsedData);
        
        console.log(`Worker: Processing complete in ${Date.now() - startTime}ms.`);
        
        // Return metrics payload to main thread
        self.postMessage({ type: 'COMPLETE', metrics });
    }
});

function executeHeavyAnalysisBackground(data) {
    const start = Date.now();
    // Simulate computational heavy loop on background thread
    while (Date.now() - start < 1500) {
        // The main thread remains responsive at 60fps during this calculation!
    }
    return { length: data.length, status: "SUCCESS" };
}
