function createCounter() {
    let count = 0; // Allocated on V8 heap because inner reads it by reference
    
    return {
        increment: () => {
            count++;
            console.log(`Current Count: ${count}`);
        },
        read: () => count
    };
}

const counter = createCounter();
counter.increment(); // "Current Count: 1"
counter.increment(); // "Current Count: 2"
