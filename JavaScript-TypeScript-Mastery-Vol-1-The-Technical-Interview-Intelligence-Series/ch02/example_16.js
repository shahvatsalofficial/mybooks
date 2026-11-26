// High-Performance Event Delegation Engine
class HighDensityDataGrid {
    constructor(containerId) {
        this.gridContainer = document.getElementById(containerId);
        this.initEventListeners();
    }

    initEventListeners() {
        // Attach a single listener to the grid container
        this.gridContainer.addEventListener('click', (event) => {
            // Find the closest table cell element (event delegation target)
            const targetCell = event.target.closest('.grid-cell');
            
            if (!targetCell || !this.gridContainer.contains(targetCell)) {
                return; // Event ignored (click occurred outside target cells)
            }

            this.handleCellInteraction(targetCell);
        });
    }

    handleCellInteraction(cell) {
        const rowId = cell.dataset.rowId;
        const colId = cell.dataset.colId;
        console.log(`Cell Clicked: Row ${rowId}, Col ${colId}`);
    }
}
