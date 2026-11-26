console.log("Start");

setTimeout(() => {
    console.log("Timeout 1");
    Promise.resolve().then(() => console.log("Promise Inside Timeout"));
}, 0);

process.nextTick(() => {
    console.log("nextTick 1");
    process.nextTick(() => console.log("Nested nextTick"));
});

Promise.resolve().then(() => {
    console.log("Promise 1");
    Promise.resolve().then(() => console.log("Nested Promise"));
});

process.nextTick(() => {
    console.log("nextTick 2");
});

console.log("End");
