let leakInstance = null;

function leakRegistry() {
    const massiveDataPayload = new Array(10000000).fill("LEAK");
    const originalInstance = leakInstance;
    
    // Unused closure that references 'originalInstance'
    const unusedClosure = function() {
        if (originalInstance) {
            console.log("Checking history...");
        }
    };
    
    // Active closure that gets assigned globally
    leakInstance = {
        name: "RegistryNode",
        executeAction: function() {
            // This closure shares the exact same Lexical Environment as 'unusedClosure'
            // Because 'unusedClosure' references 'originalInstance', the entire outer environment record is retained,
            // creating a linked chain of massive payload arrays that can never be garbage collected.
            return "Active";
        }
    };
}

setInterval(leakRegistry, 100); // Heap memory will explode rapidly!
