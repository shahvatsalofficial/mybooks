// Vulnerable Implementation: triggering Layout Thrashing
function vulnerableResizeGrid(elements) {
    for (let i = 0; i < elements.length; i++) {
        // READ: Forces synchronous layout calculation (Reflow!)
        const parentWidth = elements[i].parentElement.offsetWidth; 
        
        // WRITE: Mutates the DOM geometry
        elements[i].style.width = (parentWidth * 0.8) + 'px'; 
    }
}
