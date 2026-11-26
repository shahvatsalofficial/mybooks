// Safely batch data inside a transaction using small dynamic microtasks
async function batchWriteResilient(db, storeName, records) {
    const transaction = db.transaction([storeName], "readwrite");
    const store = transaction.objectStore(storeName);
    
    // Batch updates asynchronously in small chunks
    for (const record of records) {
        store.put(record);
        // Yield execution to the main thread to prevent UI freezing
        await new Promise((resolve) => setTimeout(resolve, 0));
    }
}
