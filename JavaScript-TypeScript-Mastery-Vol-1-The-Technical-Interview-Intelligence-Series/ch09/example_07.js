// Strong Map Reference prevents garbage collection of keys
const activeMap = new Map();
let keyObject = { id: 100 };
activeMap.set(keyObject, "Critical Metadata");
keyObject = null; // KeyObject remains in memory because Map retains a strong reference!

// WeakMap reference allows garbage collection of keys
const activeWeakMap = new WeakMap();
let keyObjectSafe = { id: 200 };
activeWeakMap.set(keyObjectSafe, "Transient Metadata");
keyObjectSafe = null; // KeyObjectSafe is swept from memory in the next GC cycle!
