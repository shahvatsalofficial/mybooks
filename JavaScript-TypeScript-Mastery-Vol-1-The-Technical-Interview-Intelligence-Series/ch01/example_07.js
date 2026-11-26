// 1. Function Declaration Hoisting
executeQuery(); // "Query Executed Successfully" (Hoisted fully!)
function executeQuery() {
    console.log("Query Executed Successfully");
}

// 2. Function Expression Hoisting
runDiagnostics(); // TypeError: runDiagnostics is not a function (declared via var, initialized to undefined)
var runDiagnostics = function() {
    console.log("Diagnostics Complete");
};
