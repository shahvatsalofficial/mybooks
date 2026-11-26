console.log("CP_1:", globalName); 
try {
    console.log("CP_2:", blockUser);
} catch (e) {
    console.log("CP_2: Caught ReferenceError");
}

var globalName = "Enterprise_JS";
let blockUser = "Vatsal_Shah";

function runVerification() {
    console.log("CP_3:", localScope);
    var localScope = "VerificationPassed";
    
    if (true) {
        let localScope = "BlockOverridden";
        console.log("CP_4:", localScope);
    }
    console.log("CP_5:", localScope);
}
runVerification();
