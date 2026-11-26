// Slow, sluggish grid updater
function forceGlobalGridUpdate(gridCells) {
    gridCells.forEach(cell => {
        // READ: Forces synchronous style/layout calculation
        const cellOffsetLeft = cell.offsetLeft; 
        
        // WRITE: Modifies layout dynamically, dirtying the layout
        const computedMargin = cellOffsetLeft * 0.05;
        cell.style.marginLeft = computedMargin + 'px';
        
        // READ: Forces another synchronous reflow
        const computedHeight = cell.getBoundingClientRect().height;
        
        // WRITE: Modifies style, dirtying layout again
        cell.style.paddingTop = (computedHeight * 0.1) + 'px';
    });
}
