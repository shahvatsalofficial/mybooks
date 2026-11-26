import { Worker } from 'worker_threads';
import { resolve } from 'path';

// Allocate 4 bytes of shared memory (enough for one 32-bit integer)
const sharedBuffer = new SharedArrayBuffer(4);

// Create a view on the buffer to read it as a 32-bit signed integer array
const counterView = new Int32Array(sharedBuffer);
counterView[0] = 0; // Initialize counter at index 0 to 0

console.log(`[Main] Shared memory initialized. Initial count: ${counterView[0]}`);

const workerPath = resolve(__dirname, './app_worker.js');

// Spawn two worker threads and pass them the shared buffer
const worker1 = new Worker(workerPath, { workerData: { sharedBuffer } });
const worker2 = new Worker(workerPath, { workerData: { sharedBuffer } });

let workersCompleted = 0;

const handleWorkerExit = () => {
    workersCompleted++;
    if (workersCompleted === 2) {
        // Both threads have finished executing
        console.log(`[Main] Task complete. Final synchronized count: ${counterView[0]}`);
    }
};

worker1.on('exit', handleWorkerExit);
worker2.on('exit', handleWorkerExit);
