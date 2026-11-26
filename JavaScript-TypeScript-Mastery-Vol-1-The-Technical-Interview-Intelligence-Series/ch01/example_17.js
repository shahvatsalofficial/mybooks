function initializeDataRouterRefactored() {
    let interactionCounter = 0;
    
    // Explicitly scope the large payload allocation away from long-lived closures
    (function performInitialization() {
        let largePayload = new Array(5000000).fill("STR_DATA");
        // Perform initial diagnostics setup within an isolated context
        console.log("Diag completed, payload processed.");
    })(); 
    
    // The returned closure only retains references to 'interactionCounter'
    return {
        incrementCalls: function() {
            interactionCounter++;
            return interactionCounter;
        }
    };
}
const activeRouterFixed = initializeDataRouterRefactored();
// largePayload is reclaimed by the garbage collector immediately after performInitialization completes.
