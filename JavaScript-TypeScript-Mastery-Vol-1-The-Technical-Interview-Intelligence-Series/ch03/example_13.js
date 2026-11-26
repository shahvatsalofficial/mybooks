// worker.js: Receiving the Transferred Buffer
self.addEventListener('message', (event) => {
    const buffer = event.data.payload;
    console.log(buffer.byteLength); // Outputs 50000000 (50MB resolved instantly!)
    
    const dataView = new Int32Array(buffer);
    // Perform computational logic on the background thread...
});
