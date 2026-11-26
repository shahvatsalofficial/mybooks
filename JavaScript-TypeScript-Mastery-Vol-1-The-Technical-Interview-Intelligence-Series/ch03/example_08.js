// Vulnerable Implementation: Creating a Detached DOM Leak
let globalCache = [];

function createAndLeakElement() {
    const parentContainer = document.createElement('div');
    parentContainer.className = 'heavy-dashboard-panel';
    
    for (let i = 0; i < 1000; i++) {
        const childNode = document.createElement('span');
        childNode.textContent = `Telemetry Row: ${i}`;
        parentContainer.appendChild(childNode);
    }
    
    // The node is appended to the visible document
    document.body.appendChild(parentContainer);
    
    // The node is removed from the document
    document.body.removeChild(parentContainer);
    
    // VULNERABILITY: Storing a reference to the removed DOM element in a global variable
    globalCache.push(parentContainer); 
}
