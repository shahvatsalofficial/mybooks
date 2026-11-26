// Optimized grid updater: batching reads and deferring writes
function optimizedGlobalGridUpdate(gridCells) {
    // 1. Batch all geometry READ operations in a single pass
    const cellGeometries = gridCells.map(cell => {
        return {
            offsetLeft: cell.offsetLeft,
            height: cell.getBoundingClientRect().height
        };
    });

    // 2. Schedule all WRITE mutations within requestAnimationFrame
    requestAnimationFrame(() => {
        gridCells.forEach((cell, index) => {
            const geometry = cellGeometries[index];
            const computedMargin = geometry.offsetLeft * 0.05;
            const computedPadding = geometry.height * 0.1;

            // Batch writes consecutively
            cell.style.marginLeft = computedMargin + 'px';
            cell.style.paddingTop = computedPadding + 'px';
        });
    });
}
