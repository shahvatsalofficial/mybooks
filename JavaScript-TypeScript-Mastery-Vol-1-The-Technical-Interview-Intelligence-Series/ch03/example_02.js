function workLoopConcurrent() {
    // Perform work until there are no nodes left OR the browser frame deadline is hit
    while (workInProgress !== null && !shouldYieldToBrowser()) {
        workInProgress = performUnitOfWork(workInProgress);
    }
}
