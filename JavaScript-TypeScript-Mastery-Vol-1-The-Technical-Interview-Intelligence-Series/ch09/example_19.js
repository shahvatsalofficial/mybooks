// Hardened Garbage-Safe Pattern
function createAndPruneElement() {
    const list = document.createElement("ul");
    for (let i = 0; i < 1000; i++) {
        const item = document.createElement("li");
        list.appendChild(item);
    }
    document.body.appendChild(list);
    document.body.removeChild(list);
    
    // Explicitly break the global reference pointer
    cacheNode = null;
}
