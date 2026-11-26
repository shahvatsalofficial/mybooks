// Optimized Implementation: Batched Execution
function batchedResizeGrid(elements) {
    // 1. Batch all READ operations cleanly
    const parentWidths = elements.map(el => el.parentElement.offsetWidth);
    
    // 2. Batch all WRITE operations, deferring writes to requestAnimationFrame
    requestAnimationFrame(() => {
        elements.forEach((el, index) => {
            el.style.width = (parentWidths[index] * 0.8) + 'px';
        });
    });
}
