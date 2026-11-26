import { workerData } from 'worker_threads';

const sharedBuffer: SharedArrayBuffer = workerData.sharedBuffer;
const counterView = new Int32Array(sharedBuffer);

console.log(`[Worker - ${process.pid}] Worker thread initialized. Accessing shared memory.`);

for (let i = 0; i < 500000; i++) {
    // DANGER: counterView[0]++ is vulnerable to race conditions.
    // Instead, perform an atomic increment operation.
    Atomics.add(counterView, 0, 1);
}

console.log(`[Worker - ${process.pid}] Thread task complete.`);
