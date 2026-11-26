import { Worker } from 'worker_threads';
import { resolve } from 'path';

export class CryptoPoolManager {
    private sharedBuffer: SharedArrayBuffer;
    private stateArray: Int32Array;
    private worker: Worker;

    constructor() {
        // Allocate 12 bytes of shared memory:
        // Byte 0: Worker state lock status (0 = Idle, 1 = Processing, 2 = Data Ready)
        // Byte 4-11: Data input slots for cryptographic values
        this.sharedBuffer = new SharedArrayBuffer(12);
        this.stateArray = new Int32Array(this.sharedBuffer);
        
        // Initialize state to 0 (Idle)
        this.stateArray[0] = 0;

        const workerPath = resolve(__dirname, './engine_worker.js');
        
        // Spawn the worker thread and pass the shared buffer
        this.worker = new Worker(workerPath, {
            workerData: { sharedBuffer: this.sharedBuffer }
        });
    }

    public async executeHash(inputValue: number): Promise<number> {
        return new Promise((resolve) => {
            // Write input data directly to the shared memory buffer (Byte 1 = slot index 1)
            this.stateArray[1] = inputValue;

            // Set state flag to 1 (Processing)
            Atomics.store(this.stateArray, 0, 1);

            // Notify the worker thread that data is ready
            Atomics.notify(this.stateArray, 0, 1);

            // Poll or wait for the worker to signal completion
            const checkStatus = () => {
                // Atomically read the state flag
                const state = Atomics.load(this.stateArray, 0);
                if (state === 2) {
                    // Data is processed and ready (state = 2). Read result from index 2.
                    const result = this.stateArray[2];
                    
                    // Reset worker state to 0 (Idle)
                    Atomics.store(this.stateArray, 0, 0);
                    resolve(result);
                } else {
                    // Yield execution and check again on the next tick
                    setImmediate(checkStatus);
                }
            };
            
            checkStatus();
        });
    }

    public terminate() {
        this.worker.terminate();
    }
}
