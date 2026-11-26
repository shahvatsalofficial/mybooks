function allocateSecureTransaction() {
    const massiveHeapPayload = new Array(10000000); // 10 Million array elements
    
    const status = "Transaction Active";
    
    // This closure captures the small string 'status', but keeps the entire
    // scope context frame (including massiveHeapPayload) alive on the heap!
    return function checkStatus() {
        return status;
    };
}
