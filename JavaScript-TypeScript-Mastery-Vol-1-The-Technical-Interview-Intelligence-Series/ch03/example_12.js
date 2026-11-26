// Main Thread: Transferring an ArrayBuffer
const dataBuffer = new ArrayBuffer(50000000); // Allocate a 50MB buffer
const view = new Int32Array(dataBuffer);
view.fill(999);

// Schedule worker thread execution
const worker = new Worker('processor.js');

// Pass the buffer as a Transferable Object.
// The first argument is the message payload; the second is an array of objects to transfer.
worker.postMessage({ payload: dataBuffer }, [dataBuffer]);

// VERIFICATION: The buffer on the main thread is now cleared
console.log(dataBuffer.byteLength); // Outputs 0!
