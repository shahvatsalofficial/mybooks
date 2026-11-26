// Leaky Detached DOM Pattern
let cacheNode = null;

function createAndLeakElement() {
    const list = document.createElement("ul");
    for (let i = 0; i < 1000; i++) {
        const item = document.createElement("li");
        list.appendChild(item);
    }
    // We attach the list to the DOM
    document.body.appendChild(list);
    
    // We preserve a reference to a child node in global scope
    cacheNode = list.firstChild;
    
    // We remove the list from the DOM
    document.body.removeChild(list);
}
