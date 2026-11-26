// Vulnerable Closure Leak
// The stale closure retains a large array reference in memory because
// it shares the same parent scope context as the active execution method.
let leakHolder = null;

function runLeakyTransaction() {
    const massiveAsset = new Array(10000000).fill("STALE_DATA");
    const previousHolder = leakHolder;

    leakHolder = function() {
        if (previousHolder) {
            console.log("Prior connection exists");
        }
    };
}
