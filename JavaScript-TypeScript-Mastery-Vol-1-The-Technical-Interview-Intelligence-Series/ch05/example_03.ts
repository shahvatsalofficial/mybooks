function executeCallbacksWithVar() {
    const callbacks = [];
    
    for (var i = 0; i < 3; i++) {
        // 'var' is function-scoped. There is only one physical 'i' variable
        // shared across all callback closures.
        callbacks.push(() => console.log(i));
    }
    
    callbacks.forEach(cb => cb());
}

executeCallbacksWithVar();
// Output:
// 3
// 3
// 3
