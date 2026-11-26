class HighPerformanceLogAnalyzer {
    constructor() {
        // Initialize Web Worker instance
        this.worker = new Worker('log_worker.js');
        this.setupWorkerListeners();
    }

    setupWorkerListeners() {
        this.worker.onmessage = (event) => {
            const { type, metrics } = event.data;
            if (type === 'COMPLETE') {
                this.renderOutput(metrics);
            }
        };
        
        this.worker.onerror = (err) => {
            console.error(`Worker Execution Error: ${err.message}`);
        };
    }

    processLogUpload(filePayload) {
        const reader = new FileReader();
        
        reader.onload = (event) => {
            const rawString = event.target.result;
            
            // RESOLVED: Convert raw string into Uint8Array buffer for Transferable transmission
            const encoder = new TextEncoder();
            const rawBuffer = encoder.encode(rawString).buffer; // Retrieve the underlying ArrayBuffer
            
            console.log(`Sending data: ${rawBuffer.byteLength} bytes to background thread.`);
            
            // RESOLVED: Transfer buffer instantly with zero copy.
            // The buffer is passed inside the transferable array (second argument)
            this.worker.postMessage({ type: 'PROCESS', buffer: rawBuffer }, [rawBuffer]);
            
            // VERIFICATION: Buffer is detached and occupies 0 bytes on the main thread
            console.log(`Main thread buffer verification size: ${rawBuffer.byteLength}`); 
        };
        
        reader.readAsArrayBuffer(filePayload);
    }

    renderOutput(metrics) {
        console.log(`Zero-Copy background run complete. Result metrics status: ${metrics.status}`);
    }
}
