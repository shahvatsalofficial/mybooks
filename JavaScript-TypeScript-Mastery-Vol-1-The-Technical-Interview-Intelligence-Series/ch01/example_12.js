function starveCPU() {
    Promise.resolve().then(() => {
        // Enqueue another microtask immediately
        starveCPU(); 
    });
}
// If executed, the macrotask queue (timers, clicks) will be completely frozen,
// and the main browser rendering thread will hang.
