// Verification of physical linkages
console.log(lead.__proto__ === Developer.prototype); // true
console.log(Developer.prototype.__proto__ === Object.prototype); // true
console.log(Object.prototype.__proto__ === null); // true
console.log(Developer.__proto__ === Function.prototype); // true
