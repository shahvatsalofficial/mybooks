// Vulnerable Shape Mutation Pattern (Unoptimized shape transitions)
// V8 must continuously compile new hidden classes due to mismatched assignments.
function createUserBad(id, name) {
    const user = {};
    if (id) {
        user.id = id; // Transition 1: Shape A -> Shape B
    }
    user.name = name; // Transition 2: Shape B -> Shape C or Shape A -> Shape D
    return user;
}

// Hardened Optimization Pattern (Static Shape Alignment)
// By using constructor initializations or class declarations, we ensure 
// all instances share the EXACT same hidden class, allowing V8 Inline Caches to optimize.
class HardenedUserOptimized {
    constructor(id = null, name = "Default") {
        this.id = id;      // Shape holds constant "id" key index pointer
        this.name = name;  // Shape holds constant "name" key index pointer
    }
}
