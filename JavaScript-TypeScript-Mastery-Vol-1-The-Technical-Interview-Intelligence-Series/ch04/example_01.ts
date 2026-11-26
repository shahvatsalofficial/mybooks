import { writeFileSync } from 'fs';

console.log('1. Call Stack Start');

setTimeout(() => {
    console.log('2. Timer 1 (Macrotask)');
    process.nextTick(() => console.log('3. nextTick inside Timer 1 (Microtask)'));
    Promise.resolve().then(() => console.log('4. Promise inside Timer 1 (Microtask)'));
}, 0);

setImmediate(() => {
    console.log('5. Immediate 1 (Macrotask)');
    Promise.resolve().then(() => console.log('6. Promise inside Immediate 1 (Microtask)'));
});

Promise.resolve().then(() => {
    console.log('7. Main Promise (Microtask)');
    process.nextTick(() => console.log('8. nextTick nested in Main Promise (Microtask)'));
});

process.nextTick(() => {
    console.log('9. Main nextTick (Microtask)');
});

console.log('10. Call Stack End');
