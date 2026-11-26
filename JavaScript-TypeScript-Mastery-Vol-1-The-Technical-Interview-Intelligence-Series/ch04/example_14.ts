import { workerData } from 'worker_threads';

const sharedBuffer: SharedArrayBuffer = workerData.sharedBuffer;
const stateArray = new Int32Array(sharedBuffer);

console.log(`[Worker] Cryptographic thread spawned successfully.`);

const runWorkerLoop = () => {
    while (true) {
        // Wait atomically until index 0 (state flag) changes to 1 (Processing).
        // If state is 0, the thread goes to sleep, consuming 0% CPU.
        Atomics.wait(stateArray, 0, 0);

        // Retrieve the input data from shared memory (index 1)
        const inputData = Atomics.load(stateArray, 1);

        // Perform the CPU-heavy cryptographic hashing operation
        const result = computeComplexHash(inputData);

        // Store the result directly in shared memory (index 2)
        stateArray[2] = result;

        // Set the state flag to 2 (Data Ready)
        Atomics.store(stateArray, 0, 2);

        // Notify the main dispatcher thread that the result is ready
        Atomics.notify(stateArray, 0, 1);
    }
};

function computeComplexHash(data: number): number {
    let hash = data;
    // Simulate a heavy CPU hashing load
    for (let i = 0; i < 1000000; i++) {
        hash = (hash ^ i) + (hash << 5) + 79;
    }
    return hash;
}

runWorkerLoop();
