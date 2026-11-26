// V8 Compilation Mechanics Demonstration
function demonstrateTDZ() {
    // V8 Hoists both 'a' and 'b', but handles their registers differently.
    // 'a' is initialized to undefined.
    // 'b' is placed in an "uninitialized" state in the Lexical Environment.
    
    console.log(a); // Prints: undefined
    try {
        console.log(b); // Throws: ReferenceError: Cannot access 'b' before initialization
    } catch(e) {}
    
    var a = 1;
    let b = 2;
}
