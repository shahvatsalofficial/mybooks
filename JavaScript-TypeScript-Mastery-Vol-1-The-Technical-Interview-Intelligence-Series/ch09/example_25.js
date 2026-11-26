// MainThread.js
const canvas = document.getElementById("heavy-render");
const offscreen = canvas.transferControlToOffscreen();
const worker = new Worker("renderWorker.js");

// Transfer control to worker thread
worker.postMessage({ canvas: offscreen }, [offscreen]);
