// Conceptual V8 Desugaring representation
{
    let i_outer = 0;
    while (i_outer < 3) {
        // A new lexical environment is allocated for every single iteration
        const i_current = i_outer; 
        
        callbacks.push(() => {
            // The closure captures the isolated i_current variable,
            // not the mutable loop counter i_outer.
            console.log(i_current);
        });
        
        i_outer = i_current + 1;
    }
}
