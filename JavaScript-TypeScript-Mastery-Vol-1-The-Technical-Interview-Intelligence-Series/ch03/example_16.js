// Vulnerable Single-Threaded Logger: processing large datasets on the main thread
class LogAnalyzer {
    constructor() {
        this.recordsCache = [];
    }

    processLogUpload(filePayload) {
        const reader = new FileReader();
        
        reader.onload = (event) => {
            // Retrieve string data from raw upload
            const rawString = event.target.result;
            
            // VULNERABILITY: Parsing massive JSON payloads blocks the main thread
            const parsedData = JSON.parse(rawString);
            
            // Executing heavy analysis algorithms synchronously on the parsed payload
            const diagnosticMetrics = this.executeHeavyAnalysis(parsedData);
            
            this.renderOutput(diagnosticMetrics);
        };
        
        reader.readAsText(filePayload);
    }

    executeHeavyAnalysis(data) {
        // Simple representation of heavy computational CPU loops
        const start = Date.now();
        while (Date.now() - start < 1500) {
            // Block main thread for 1.5 seconds to simulate calculation workload
        }
        return { length: data.length, status: "SUCCESS" };
    }

    renderOutput(metrics) {
        console.log(`Processing complete: ${metrics.length} logs evaluated.`);
    }
}
