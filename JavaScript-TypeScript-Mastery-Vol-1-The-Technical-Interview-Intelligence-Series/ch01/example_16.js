function initializeDataRouter() {
    let largePayload = new Array(5000000).fill("STR_DATA");
    let interactionCounter = 0;
    
    const monitorLogger = function() {
        if (largePayload) {
            console.log("Diagnostics active.");
        }
    };
    
    return {
        incrementCalls: function() {
            // This active closure does not use largePayload
            interactionCounter++;
            return interactionCounter;
        }
    };
}
const activeRouter = initializeDataRouter();
