// Safe from stale closures: The updater function receives the real-time state value directly from React
setCount(prevCount => prevCount + 1);
